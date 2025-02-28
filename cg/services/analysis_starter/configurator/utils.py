import copy
import re
from pathlib import Path

import rich_click as click

from cg.constants.priority import Priority, SlurmQos
from cg.io.txt import write_txt
from cg.meta.workflow.utils.utils import are_all_samples_control
from cg.store.models import Case


def write_content_to_file_or_stdout(content: str, file_path: Path, dry_run: bool = False) -> None:
    """Write content to a file if dry-run is False, otherwise print to stdout."""
    if dry_run:
        click.echo(content)
        return
    write_txt(content=content, file_path=file_path)


def get_slurm_qos_for_case(case: Case) -> str:
    """Get Quality of service (SLURM QOS) for the case."""
    if are_all_samples_control(case=case):
        return SlurmQos.EXPRESS
    return Priority.priority_to_slurm_qos().get(case.priority)


def replace_values_in_params_file(workflow_parameters: dict) -> dict:
    """
    Iterate through the dictionary until all placeholders are replaced with the corresponding value
    from the dictionary
    """
    replaced_workflow_parameters = copy.deepcopy(workflow_parameters)
    while True:
        resolved: bool = True
        for key, value in replaced_workflow_parameters.items():
            new_value: str | int = replace_params_placeholders(value, workflow_parameters)
            if new_value != value:
                resolved = False
                replaced_workflow_parameters[key] = new_value
        if resolved:
            break
    return replaced_workflow_parameters


def replace_params_placeholders(value: str | int, workflow_parameters: dict) -> str:
    """Replace values marked as placeholders with values from the given dictionary"""
    if isinstance(value, str):
        placeholders: list[str] = re.findall(r"{{\s*([^{}\s]+)\s*}}", value)
        for placeholder in placeholders:
            if placeholder in workflow_parameters:
                value = value.replace(
                    f"{{{{{placeholder}}}}}", str(workflow_parameters[placeholder])
                )
    return value
