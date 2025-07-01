import copy
import re


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
