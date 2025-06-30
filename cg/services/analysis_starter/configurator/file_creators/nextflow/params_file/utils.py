import copy
import logging
import re

from cg.exc import CgDataError

LOG = logging.getLogger(__name__)


def replace_values_in_params_file(workflow_parameters: dict) -> dict:
    """
    Iterate through the dictionary until all placeholders are replaced with the corresponding value
    from the dictionary
    """
    replaced_workflow_parameters = copy.deepcopy(workflow_parameters)
    while True:
        resolved: bool = True
        for key, value in replaced_workflow_parameters.items():
            new_value: str | int = _replace_params_placeholders(value, workflow_parameters)
            if new_value != value:
                resolved = False
                replaced_workflow_parameters[key] = new_value
        if resolved:
            break
    return replaced_workflow_parameters


def _replace_params_placeholders(value: str | int, workflow_parameters: dict) -> str:
    """Replace values marked as placeholders with values from the given dictionary"""
    if isinstance(value, str):
        placeholders: list[str] = re.findall(r"{{\s*([^{}\s]+)\s*}}", value)
        for placeholder in placeholders:
            if placeholder in workflow_parameters:
                value = value.replace(
                    f"{{{{{placeholder}}}}}", str(workflow_parameters[placeholder])
                )
    return value


def validate_no_repeated_parameters(case_parameters: dict, workflow_parameters: dict) -> None:
    """
    Validate that no parameter is defined twice with different values in  the case and workflow
    parameter dictionaries.
    Raises:
        CgDataError: if one or more parameters are defined with different values in the
        case and workflow parameters.
    """
    error: bool = False
    repeated_parameters = set(case_parameters.keys()) & set(workflow_parameters.keys())
    for param in repeated_parameters:
        if case_parameters[param] != workflow_parameters[param]:
            LOG.error(
                f"Parameter '{param}' is defined with different values in the case and "
                f"workflow parameters.\n Case parameter value: {case_parameters[param]} \n"
                f"Workflow parameter value: {workflow_parameters[param]}"
            )
            error = True
    if error:
        raise CgDataError(
            "One or more parameters are defined with different values "
            "in the case and workflow parameters."
        )
