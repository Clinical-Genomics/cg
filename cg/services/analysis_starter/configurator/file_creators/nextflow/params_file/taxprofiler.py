import logging
from pathlib import Path

from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.models import (
    TaxprofilerParameters,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
)

LOG = logging.getLogger(__name__)


class TaxprofilerParamsFileCreator(ParamsFileCreator):

    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> None:
        LOG.debug(f"Creating params file for case {case_id}")
        content: dict = self._get_content(
            case_run_directory=file_path.parent, sample_sheet_path=sample_sheet_path
        )
        write_yaml_nextflow_style(file_path=file_path, content=content)

    def _get_content(self, case_run_directory: Path, sample_sheet_path: Path) -> dict:
        """Return the merged dictionary with case-specific parameters and workflow parameters."""
        case_parameters = TaxprofilerParameters(
            input=sample_sheet_path,
            outdir=case_run_directory,
        )
        workflow_parameters: dict = read_yaml(self.params)
        parameters: dict = case_parameters.model_dump() | workflow_parameters
        curated_parameters: dict = replace_values_in_params_file(parameters)
        return curated_parameters
