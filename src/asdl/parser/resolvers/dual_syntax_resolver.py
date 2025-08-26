"""
Dual syntax resolution for parameters/params and variables/vars fields.

Extracts dual syntax resolution functionality from the monolithic parser
with exact preservation of business logic and P301/P302 warning generation.
"""

from typing import Dict, Any, Optional, List

from ...data_structures import Locatable
from ...diagnostics import Diagnostic, DiagnosticSeverity


class DualSyntaxResolver:
    """Handles dual syntax resolution for parameters/params and variables/vars fields."""
    
    @staticmethod
    def resolve_parameters(data: Dict[str, Any], context: str, diagnostics: List[Diagnostic], loc: Locatable) -> Optional[Dict[str, Any]]:
        """
        Resolve parameters field with dual syntax support.
        
        Supports both 'parameters' (canonical) and 'params' (abbreviated).
        Generates warning if both are present.
        
        Exact implementation from _resolve_parameters_field() method.
        Preserves all existing business logic and diagnostics.
        
        Args:
            data: Dictionary containing module/instance data
            context: Context string for error messages (e.g., "Module 'test_mod'")
            diagnostics: List to append warnings to
            loc: Location information for diagnostics
            
        Returns:
            Resolved parameters dictionary or None if neither field present
        """
        parameters = data.get('parameters')
        params = data.get('params')
        
        if parameters is not None and params is not None:
            # Both forms present - generate warning and prefer canonical
            diagnostics.append(Diagnostic(
                code="P0601",
                title="Dual Parameter Syntax",
                details=f"{context} contains both 'parameters' and 'params' fields. Using 'parameters' and ignoring 'params'.",
                severity=DiagnosticSeverity.WARNING,
                location=loc,
                suggestion="Use either 'parameters' (canonical) or 'params' (abbreviated), but not both."
            ))
            return parameters
        elif parameters is not None:
            return parameters
        elif params is not None:
            return params
        else:
            return None

    @staticmethod
    def resolve_variables(data: Dict[str, Any], context: str, diagnostics: List[Diagnostic], loc: Locatable) -> Optional[Dict[str, Any]]:
        """
        Resolve variables field with dual syntax support.
        
        Supports both 'variables' (canonical) and 'vars' (abbreviated).
        Generates warning if both are present.
        
        Exact implementation from _resolve_variables_field() method.
        Preserves all existing business logic and diagnostics.
        
        Args:
            data: Dictionary containing module data  
            context: Context string for error messages (e.g., "Module 'test_mod'")
            diagnostics: List to append warnings to
            loc: Location information for diagnostics
            
        Returns:
            Resolved variables dictionary or None if neither field present
        """
        variables = data.get('variables')
        vars_abbrev = data.get('vars')
        
        if variables is not None and vars_abbrev is not None:
            # Both forms present - generate warning and prefer canonical
            diagnostics.append(Diagnostic(
                code="P0602",
                title="Dual Variables Syntax",
                details=f"{context} contains both 'variables' and 'vars' fields. Using 'variables' and ignoring 'vars'.",
                severity=DiagnosticSeverity.WARNING,
                location=loc,
                suggestion="Use either 'variables' (canonical) or 'vars' (abbreviated), but not both."
            ))
            return variables
        elif variables is not None:
            return variables
        elif vars_abbrev is not None:
            return vars_abbrev
        else:
            return None