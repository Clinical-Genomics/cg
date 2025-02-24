from cg.constants import Priority
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class RarediseaseCaseConfig(CaseConfig):
    case_priority: Priority
    netxflow_config_file: str
    params_file: str
    work_dir: str
