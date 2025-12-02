from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class NextflowCaseConfig(CaseConfig):
    case_priority: SlurmQos
    config_profiles: list[str]
    nextflow_config_file: str
    params_file: str
    pipeline_repository: str
    pre_run_script: str
    resume: bool = False
    revision: str
    session_id: str | None = None
    work_dir: str
    workflow_id: str | None = None

    def get_session_id(self) -> str | None:
        return self.session_id

    def get_workflow_id(self) -> str | None:
        return self.workflow_id
