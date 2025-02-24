from pathlib import Path

from cg.constants import Priority
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class RarediseaseCaseConfig(CaseConfig):
    case_priority: Priority
    nextflow_config_file: Path
    params_file: Path
    work_dir: Path
