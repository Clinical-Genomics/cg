from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig


class RarediseaseConfigurator(Configurator):

    def create_config(self, case_id: str) -> RarediseaseCaseConfig:
        return RarediseaseCaseConfig(
            case_id=case_id,
            workflow="raredisease",
            compute_env="raredisease",
            config_file="raredisease",
            params_file="raredisease",
            revision="raredisease",
            work_dir="raredisease",
        )
