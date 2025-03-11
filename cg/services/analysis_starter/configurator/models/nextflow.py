from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class NextflowCaseConfig(CaseConfig):
    case_priority: SlurmQos
    nextflow_config_file: str
    params_file: str
    work_dir: str
