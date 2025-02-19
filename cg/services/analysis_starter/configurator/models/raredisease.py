from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class RarediseaseCaseConfig(CaseConfig):
    compute_env: str
    config_file: str
    params_file: str
    revision: str
    work_dir: str
