from typing import List, Tuple, Dict, Any, Optional

from ..data_structures import Instance, Locatable
from ..diagnostics import Diagnostic, DiagnosticSeverity


class VariableResolver:
    """
    Handles variable resolution in instance parameters.
    
    Resolves direct variable references in instance parameter values using
    the module's variables dictionary. Uses simple string matching for
    variable name resolution.
    """

    def resolve_instance_variables(
        self, 
        instances: Dict[str, Instance], 
        variables: Dict[str, Any], 
        module_name: str
    ) -> Tuple[Dict[str, Instance], List[Diagnostic]]:
        """
        Resolve variable references in all instances using module variables.
        
        Args:
            instances: Dictionary of instance name to Instance objects
            variables: Dictionary of variable name to value from module
            module_name: Name of the module (for diagnostics)
            
        Returns:
            Tuple of (resolved_instances, diagnostics)
        """
        if not instances or not variables:
            return instances, []
            
        resolved_instances = {}
        diagnostics: List[Diagnostic] = []
        
        for instance_name, instance in instances.items():
            resolved_instance, instance_diagnostics = self._resolve_instance_parameters(
                instance, variables, module_name, instance_name
            )
            resolved_instances[instance_name] = resolved_instance
            diagnostics.extend(instance_diagnostics)
            
        return resolved_instances, diagnostics

    def _resolve_instance_parameters(
        self, 
        instance: Instance, 
        variables: Dict[str, Any], 
        module_name: str, 
        instance_name: str
    ) -> Tuple[Instance, List[Diagnostic]]:
        """
        Resolve variable references in a single instance's parameters.
        
        Args:
            instance: Instance object to process
            variables: Module variables dictionary
            module_name: Module name for diagnostics
            instance_name: Instance name for diagnostics
            
        Returns:
            Tuple of (resolved_instance, diagnostics)
        """
        if not instance.parameters:
            return instance, []
            
        resolved_parameters = {}
        diagnostics: List[Diagnostic] = []
        
        for param_name, param_value in instance.parameters.items():
            resolved_value, param_diagnostics = self._resolve_parameter_value(
                param_value, variables, module_name, instance_name, param_name, instance
            )
            resolved_parameters[param_name] = resolved_value
            diagnostics.extend(param_diagnostics)
        
        # Create new instance with resolved parameters
        from dataclasses import replace
        resolved_instance = replace(instance, parameters=resolved_parameters)
        
        return resolved_instance, diagnostics

    def _resolve_parameter_value(
        self, 
        value: Any, 
        variables: Dict[str, Any], 
        module_name: str, 
        instance_name: str, 
        param_name: str,
        locatable: Optional[Locatable] = None
    ) -> Tuple[Any, List[Diagnostic]]:
        """
        Resolve a single parameter value if it references a variable.
        
        Uses direct string matching - if the parameter value exactly matches
        a variable name, replace it with the variable's value.
        
        Args:
            value: Parameter value to potentially resolve
            variables: Module variables dictionary
            module_name: Module name for diagnostics
            instance_name: Instance name for diagnostics
            param_name: Parameter name for diagnostics
            locatable: Location info for diagnostics
            
        Returns:
            Tuple of (resolved_value, diagnostics)
        """
        diagnostics: List[Diagnostic] = []
        
        # Convert value to string for name matching
        try:
            str_value = str(value)
        except Exception:
            # If we can't convert to string, just return original value
            return value, diagnostics
        
        # Check if value exactly matches a variable name
        if str_value in variables:
            # Variable found - return its value
            resolved_value = variables[str_value]
            return resolved_value, diagnostics
        
        # Check if it looks like a variable reference but isn't defined
        # This helps catch typos in variable names. Be conservative to avoid
        # flagging legitimate literal strings (e.g., device/source names).
        if self._looks_like_variable_reference(str_value, variables):
            diagnostics.append(
                self._create_diagnostic(
                    "E108",
                    "Undefined Variable",
                    f"Parameter '{param_name}' in instance '{instance_name}' references undefined variable '{str_value}'. "
                    f"Available variables: {', '.join(variables.keys()) if variables else 'none'}",
                    locatable,
                )
            )
        
        # No variable match - return original value
        return value, diagnostics

    def _looks_like_variable_reference(self, value: str, variables: Dict[str, Any]) -> bool:
        """
        Heuristic to detect if a value looks like it was intended to be a variable reference.
        
        This helps catch common typos in variable names by detecting values that
        are similar to defined variable names (simple case-insensitive match).
        We intentionally avoid flagging generic identifier-like strings because
        parameters may legitimately use plain strings (e.g., source/device names).
        
        Args:
            value: String value to check
            variables: Available variables dictionary
            
        Returns:
            True if value looks like an intended variable reference
        """
        if not value or not variables:
            return False
            
        # Check for case-insensitive exact matches (common typo)
        value_lower = value.lower()
        for var_name in variables.keys():
            if var_name.lower() == value_lower and var_name != value:
                return True

        return False

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
            severity=DiagnosticSeverity.ERROR,
            location=locatable,
        )