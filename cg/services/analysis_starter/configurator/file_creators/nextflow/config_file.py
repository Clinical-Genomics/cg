import logging
from pathlib import Path

from cg.io.txt import concat_txt, write_txt
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class NextflowConfigFileCreator:

    def __init__(
        self, account: str, platform: str, resources: str, store: Store, workflow_config_path: str
    ):
        self.account = account
        self.platform = platform
        self.resources = resources
        self.store = store
        self.workflow_config_path = workflow_config_path

    def create(self, case_id: str, file_path: Path) -> None:
        """Create the Nextflow config file for a case."""
        LOG.debug(f"Creating Nextflow config file for case {case_id}")
        content: str = self._get_content(case_id)
        write_txt(file_path=file_path, content=content)

    def _get_content(self, case_id: str) -> str:
        """Get the content of the Nextflow config file."""
        config_files_list: list[str] = [
            self.platform,
            self.workflow_config_path,
            self.resources,
        ]
        case_specific_params: list[str] = [
            self._get_cluster_options(case_id),
        ]
        return concat_txt(
            file_paths=config_files_list,
            str_content=case_specific_params,
        )

    def _get_cluster_options(self, case_id: str) -> str:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return f'process.clusterOptions = "-A {self.account} --qos={case.slurm_priority}"\n'
