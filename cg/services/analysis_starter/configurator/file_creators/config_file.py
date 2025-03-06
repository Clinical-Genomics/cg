from pathlib import Path

from cg.constants import FileExtensions
from cg.io.json import write_json
from cg.io.txt import concat_txt
from cg.services.analysis_starter.configurator.file_creators.utils import get_case_id_from_path
from cg.store.models import Case
from cg.store.store import Store


class NextflowConfigFileCreator:

    def __init__(
        self, store: Store, platform: str, workflow_config_path: str, resources: str, account: str
    ):
        self.store = store
        self.platform = platform
        self.workflow_config_path = workflow_config_path
        self.resources = resources
        self.account = account

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """Return the path to the nextflow config file."""
        return Path(case_path, f"{case_id}_nextflow_config").with_suffix(FileExtensions.JSON)

    def create(self, case_id: str, case_path: Path) -> None:
        """Create the nextflow config file for a case."""
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: str = self._get_content(case_path=case_path)
        write_json(file_path=file_path, content=content)

    def _get_content(self, case_path: Path) -> str:
        """Get the content of the nextflow config file."""
        case_id: str = get_case_id_from_path(case_path)
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
