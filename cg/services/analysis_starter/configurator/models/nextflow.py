from cg.constants import Priority
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class NextflowCaseConfig(CaseConfig):
    case_priority: Priority
    nextflow_config_file: str
    params_file: str
    work_dir: str
