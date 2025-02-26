from pathlib import Path

import rich_click as click

from cg.constants.priority import Priority, SlurmQos
from cg.io.txt import write_txt
from cg.meta.workflow.utils.utils import are_all_samples_control
from cg.store.models import Case


def write_content_to_json_or_stdout(content: str, file_path: Path, dry_run: bool = False) -> None:
    """Write content to a JSON file if dry-run is False, otherwise print to stdout."""
    if dry_run:
        click.echo(content)
        return
    write_txt(content=content, file_path=file_path)


def get_slurm_qos_for_case(case: Case) -> str:
    """Get Quality of service (SLURM QOS) for the case."""
    if are_all_samples_control(case=case):
        return SlurmQos.EXPRESS
    priority: int = case.priority or Priority.research
    return Priority.priority_to_slurm_qos().get(priority)
