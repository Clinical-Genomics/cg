from pathlib import Path

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MicrosaltCaseConfig(CaseConfig):
    config_file_path: Path
