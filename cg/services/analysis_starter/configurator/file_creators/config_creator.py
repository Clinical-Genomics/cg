from cg.io.txt import concat_txt
from cg.services.analysis_starter.configurator.file_creators.abstract import FileContentCreator
from cg.store.models import Case
from cg.store.store import Store


class ConfigFileContentCreator(FileContentCreator):

    def __init__(
        self, store: Store, platform: str, workflow_config_path: str, resources: str, account: str
    ):
        self.store = store
        self.platform = platform
        self.workflow_config_path = workflow_config_path
        self.resources = resources
        self.account = account

    def create(self, case_id: str) -> str:
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
