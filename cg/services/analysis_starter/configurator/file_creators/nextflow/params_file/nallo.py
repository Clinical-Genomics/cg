import logging
from pathlib import Path
from typing import Any

from cg.constants.scout import ScoutExportFileName
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.models.nallo.nallo import NalloParameters
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
)

LOG = logging.getLogger(__name__)


class NalloParamsFileCreator(ParamsFileCreator):
    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> Any:
        LOG.debug(f"Creating params file for case {case_id}")
        content: dict = self._get_content(
            case_run_directory=file_path.parent, sample_sheet_path=sample_sheet_path
        )
        write_yaml_nextflow_style(content=content, file_path=file_path)

    def _get_content(self, case_run_directory: Path, sample_sheet_path: Path) -> dict:
        nallo_parameters = NalloParameters(
            input=sample_sheet_path,
            outdir=case_run_directory,
            filter_variants_hgnc_ids=f"{case_run_directory}/{ScoutExportFileName.PANELS_TSV}",
        )
        workflow_parameters: dict = read_yaml(self.params)
        parameters: dict = nallo_parameters.model_dump() | workflow_parameters
        curated_parameters: dict = replace_values_in_params_file(parameters)
        return curated_parameters
