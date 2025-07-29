from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class NextflowCaseConfig(CaseConfig):
    case_priority: SlurmQos
    config_profiles: list[str]
    nextflow_config_file: str
    params_file: str
    pipeline_repository: str
    pre_run_script: str
    revision: str
    work_dir: str
