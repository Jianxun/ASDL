from typing import List, Tuple, Dict, Optional
import re

from ..data_structures import Locatable
from ..diagnostics import Diagnostic, DiagnosticSeverity


class PatternExpander:
    """
    Handles pattern expansion for both literal <> and bus [] patterns.
    
    This class extracts all pattern-related functionality from the original
    elaborator to provide better separation of concerns and testability.
    """

    def has_literal_pattern(self, name: str) -> bool:
        """Check if name contains literal pattern <...>.

        Accept any input type and coerce to string to handle numeric net names (e.g., 0).
        """
        try:
            name = str(name)
        except Exception:
            return False
        # Must have both < and >
        if not ('<' in name and '>' in name):
            return False
        
        # Check that there's a complete pattern
        start = name.find('<')
        end = name.find('>')
        if start == -1 or end == -1 or start >= end:
            return False
            
        # Check for multiple bracket pairs (not supported)
        remaining = name[end+1:]
        if '<' in remaining and '>' in remaining:
            return False
            
        # Check for mixed bracket types inside pattern (array syntax inside literal)
        pattern_content = name[start+1:end]
        if '[' in pattern_content and ']' in pattern_content:
            return False
            
        # Any content inside brackets (even empty or single item) is a pattern attempt
        # Validation will enforce comma requirement
        return True

    def has_bus_pattern(self, name: str) -> bool:
        """Check if name contains bus pattern [...].

        Accept any input type and coerce to string to handle numeric net names (e.g., 0).
        """
        try:
            s = str(name)
        except Exception:
            return False
        return '[' in s and ']' in s

    def expand_literal_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []
        # Coerce to string for robust handling of non-string names
        try:
            name = str(name)
        except Exception:
            return [name], diagnostics
        match = re.search(r"^(.*?)<(.*?)>(.*?)$", name)
        if not match:
            return [name], []

        prefix, content, suffix = match.groups()

        if not content:
            diagnostics.append(
                self._create_diagnostic(
                    "E100",
                    "Empty Literal Pattern",
                    f"Pattern in '{name}' is empty.",
                    locatable,
                )
            )
            return [name], diagnostics

        items = [item.strip() for item in content.split(",")]

        # Check if ALL items are empty (which is invalid)
        if all(item == "" for item in items):
            diagnostics.append(
                self._create_diagnostic(
                    "E107",
                    "Empty Pattern Item",
                    f"Pattern in '{name}' contains only empty items.",
                    locatable,
                )
            )

        if len(items) == 1:
            diagnostics.append(
                self._create_diagnostic(
                    "E101",
                    "Single Item Pattern",
                    f"Pattern in '{name}' contains only a single item.",
                    locatable,
                )
            )

        if diagnostics:
            return [name], diagnostics

        return [f"{prefix}{item}{suffix}" for item in items], []

    def expand_bus_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        diagnostics = []
        # Coerce to string for robust handling of non-string names
        try:
            name = str(name)
        except Exception:
            return [name], diagnostics
        match = re.search(r"^(.*)\[(\d+):(\d+)\]$", name)
        if not match:
            return [name], diagnostics

        base_name, msb_str, lsb_str = match.groups()
        msb, lsb = int(msb_str), int(lsb_str)

        if msb == lsb:
            diagnostics.append(
                self._create_diagnostic(
                    "E104",
                    "Invalid Bus Range",
                    f"Bus range '{name}' has identical MSB and LSB.",
                    locatable,
                )
            )
            return [], diagnostics

        # Generate in the order specified by the pattern (MSB to LSB)
        if msb < lsb:
            # e.g., [0:3] → ["data0", "data1", "data2", "data3"]
            return [f"{base_name}{i}" for i in range(msb, lsb + 1)], diagnostics
        else:
            # e.g., [3:0] → ["data3", "data2", "data1", "data0"]  
            return [f"{base_name}{i}" for i in range(msb, lsb - 1, -1)], diagnostics

    def expand_mapping_patterns(
        self, 
        mappings: Dict[str, str], 
        original_instance_id: str, 
        expanded_instance_id: str, 
        instance_index: int
    ) -> Tuple[Dict[str, str], List[Diagnostic]]:
        """
        Expand patterns in port-to-net mappings.
        
        For instance expansion, this creates the mappings for a single expanded instance.
        """
        expanded_mappings = {}
        diagnostics: List[Diagnostic] = []
        
        # Check if the instance itself had a pattern
        instance_has_pattern = self.has_literal_pattern(original_instance_id)
        
        for port_name, net_name in mappings.items():
            # Check for patterns in port and net names
            port_has_pattern = self.has_literal_pattern(port_name)
            net_has_pattern = self.has_literal_pattern(net_name)
            
            if port_has_pattern and net_has_pattern:
                # Both sides have patterns - order-sensitive expansion
                port_items = self.extract_literal_pattern(port_name)
                net_items = self.extract_literal_pattern(net_name)
                
                # Validate pattern counts match
                if port_items and net_items and len(port_items) != len(net_items):
                    diagnostics.append(
                        self._create_diagnostic(
                            "E105",
                            "Pattern Count Mismatch",
                            f"Pattern item counts must match: {len(port_items)} vs {len(net_items)}",
                        )
                    )
                    continue
                
                # For instance expansion, select the corresponding port and net
                if instance_has_pattern and port_items and net_items:
                    # Validate that mapping patterns match instance pattern count
                    instance_items = self.extract_literal_pattern(original_instance_id)
                    if instance_items:
                        if len(instance_items) != len(port_items):
                            diagnostics.append(
                                self._create_diagnostic(
                                    "E105",
                                    "Pattern Count Mismatch",
                                    f"Instance pattern count {len(instance_items)} doesn't match port pattern count {len(port_items)}",
                                )
                            )
                            continue
                        
                        # Use the corresponding items for this instance index
                        if instance_index < len(port_items):
                            # Expand the port name using the instance pattern item
                            expanded_port = port_name.replace(f"<{','.join(port_items)}>", instance_items[instance_index])
                            # Expand the net name using the instance pattern item
                            expanded_net = net_name.replace(f"<{','.join(net_items)}>", instance_items[instance_index])
                            expanded_mappings[expanded_port] = expanded_net
                else:
                    # No instance pattern, expand all port-net pairs
                    for p, n in zip(port_items, net_items):
                        expanded_mappings[p] = n
                        
            elif port_has_pattern and not net_has_pattern:
                # Only port has pattern - expand port, use same net for all
                port_items = self.expand_literal_pattern_simple(port_name)
                for p in port_items:
                    # Coerce net name to string for robustness
                    expanded_mappings[p] = net_name if isinstance(net_name, str) else str(net_name)
                    
            elif not port_has_pattern and net_has_pattern:
                # Only net has pattern - keep port, expand net (if instance has pattern)
                if instance_has_pattern:
                    net_items = self.extract_literal_pattern(net_name)
                    instance_items = self.extract_literal_pattern(original_instance_id)
                    
                    # Validate that net pattern count matches instance pattern count
                    if net_items and instance_items and len(net_items) != len(instance_items):
                        diagnostics.append(
                            self._create_diagnostic(
                                "E105",
                                "Pattern Count Mismatch",
                                f"Pattern item counts must match: {len(instance_items)} vs {len(net_items)}",
                            )
                        )
                        continue
                    
                    if net_items and instance_index < len(net_items):
                        # Expand the net name using the instance pattern item
                        if instance_index < len(instance_items):
                            expanded_net = net_name.replace(f"<{','.join(net_items)}>", instance_items[instance_index])
                            expanded_mappings[port_name] = expanded_net
                else:
                    # No instance pattern, can't expand net pattern alone
                    diagnostics.append(
                        self._create_diagnostic(
                            "E106",
                            "Unmatched Net Pattern",
                            f"Net pattern '{net_name}' requires matching port pattern or instance pattern",
                        )
                    )
            else:
                # No patterns - keep as is, but coerce net name to string for robustness
                expanded_mappings[port_name] = net_name if isinstance(net_name, str) else str(net_name)
                
        return expanded_mappings, diagnostics

    def extract_literal_pattern(self, name: str) -> Optional[List[str]]:
        """
        Extract literal pattern items from name.
        
        Example: "in_<p,n>" -> ["p", "n"]
        Returns None if no pattern found.
        """
        if not self.has_literal_pattern(name):
            return None
        
        # Ensure we operate on a string
        name = str(name)
        start = name.find('<')
        end = name.find('>')
        pattern_content = name[start+1:end]
        
        # Handle empty pattern
        if not pattern_content:
            return []
        
        # Split by comma and strip whitespace - this handles single items too
        items = [item.strip() for item in pattern_content.split(',')]
        return items

    def expand_literal_pattern_simple(self, name: str) -> List[str]:
        """
        Expand literal pattern in name without diagnostics.
        
        Example: "in_<p,n>" -> ["in_p", "in_n"]
        Returns [name] if no pattern.
        """
        items = self.extract_literal_pattern(name)
        if items is None:
            try:
                return [str(name)]
            except Exception:
                return [name]
        
        # Find pattern location
        sname = str(name)
        start = sname.find('<')
        end = sname.find('>')
        prefix = sname[:start]
        suffix = sname[end+1:]
        
        # Generate expanded names
        expanded = []
        for item in items:
            expanded_name = prefix + item + suffix
            expanded.append(expanded_name)
        
        return expanded

    def _create_diagnostic(
        self,
        code: str,
        title: str,
        details: str,
        locatable: Optional[Locatable] = None,
    ) -> Diagnostic:
        """Helper to create a diagnostic object with location info."""
        return Diagnostic(
            code=code,
            title=title,
            details=details,
            severity=DiagnosticSeverity.ERROR, # Defaulting to ERROR for now
            location=locatable,
        )