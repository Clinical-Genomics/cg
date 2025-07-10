from pathlib import Path

from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.models import (
    RNAFusionParameters,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
)


class RNAFusionParamsFileCreator(ParamsFileCreator):

    def __init__(self, params: str):
        self.params = Path(params)

    def create(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> any:
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: dict = self._get_content(case_path=case_path, sample_sheet_path=sample_sheet_path)
        write_yaml_nextflow_style(file_path=file_path, content=content)

    def _get_content(self, case_path: Path, sample_sheet_path: Path) -> dict:
        case_parameters = RNAFusionParameters(
            input=sample_sheet_path,
            outdir=case_path,
        )
        workflow_parameters: dict = read_yaml(self.params)
        parameters: dict = case_parameters.model_dump() | workflow_parameters
        curated_parameters: dict = replace_values_in_params_file(parameters)
        return curated_parameters
