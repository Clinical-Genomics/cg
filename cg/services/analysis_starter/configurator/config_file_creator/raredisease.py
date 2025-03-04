import logging
from pathlib import Path

import rich_click as click

from cg.constants import FileExtensions
from cg.io.txt import concat_txt, write_txt
from cg.services.analysis_starter.configurator.file_creators.abstract import NextflowFileCreator
from cg.store.models import Case

LOG = logging.getLogger(__name__)


class RarediseaseNextflowConfigCreator(NextflowFileCreator):
    """Create a config file for the raredisease pipeline."""

    def __init__(
        self, store, platform: str, workflow_config_path: str, resources: str, account: str
    ):
        self.store = store
        self.platform = platform
        self.workflow_config_path = workflow_config_path
        self.resources = resources
        self.account = account

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """Get the path to the nextflow config file."""
        return Path(case_path, f"{case_id}_nextflow_config").with_suffix(FileExtensions.JSON)

    def create(self, case_id: str, case_path: Path, dry_run: bool = False) -> None:
        """Create a config file for the raredisease pipeline."""
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: str = self._get_file_content(case_id=case_id)
        self._write_content_to_file_or_stdout(content=content, file_path=file_path, dry_run=dry_run)
        LOG.debug(f"Created nextflow config file {file_path.as_posix()} successfully")

    def _get_file_content(self, case_id: str) -> str:
        """Get the content of the nextflow config file."""
        config_files_list: list[str] = [
            self.platform,
            self.workflow_config_path,
            self.resources,
        ]
        case_specific_params: list[str] = [
            self._get_cluster_options(case_id=case_id),
        ]
        return concat_txt(
            file_paths=config_files_list,
            str_content=case_specific_params,
        )

    def _get_cluster_options(self, case_id: str) -> str:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return f'process.clusterOptions = "-A {self.account} --qos={case.slurm_priority}"\n'

    @staticmethod
    def _write_content_to_file_or_stdout(content: str, file_path: Path, dry_run: bool) -> None:
        """Write content to file or stdout."""
        if dry_run:
            LOG.info(f"Dry-run: printing content to stdout. Would have written to {file_path}")
            click.echo(content)
            return
        LOG.debug(f"Writing config file to {file_path}")
        write_txt(content=content, file_path=file_path)
