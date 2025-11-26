from pathlib import Path
from typing import Any, Iterator

from cg.apps.lims import LimsAPI
from cg.constants.constants import GenomeVersion
from cg.constants.scout import ScoutExportFileName
from cg.exc import CgError
from cg.io.yaml import read_yaml
from cg.models.tomte.tomte import TomteParameters
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
)
from cg.store.store import Store


class TomteParamsFileCreator(ParamsFileCreator):
    def __init__(self, params: str, lims_api: LimsAPI, status_db: Store):
        super().__init__(params)
        self.lims_api = lims_api
        self.status_db = status_db

    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> Any:
        content: dict = self._get_content(
            case_run_directory=file_path.parent, sample_sheet_path=sample_sheet_path
        )

    def _get_content(self, case_id: str, case_run_directory: Path, sample_sheet_path: Path):
        case_parameters = TomteParameters(
            input=sample_sheet_path,
            outdir=case_run_directory,
            gene_panel_clinical_filter=Path(case_run_directory, ScoutExportFileName.PANELS),
            tissue=self._get_case_source_type(case_id),  # type:ignore
            genome=GenomeVersion.HG38,
        ).model_dump()

        workflow_params = self._get_workflow_params()
        workflow_parameters: dict = workflow_params | case_parameters
        replaced_workflow_parameters: dict = replace_values_in_params_file(
            workflow_parameters=workflow_parameters
        )

    def _get_workflow_params(self) -> dict:
        return read_yaml(self.params)

    def _get_case_source_type(self, case_id: str) -> str | None:
        """
        Return the sample source type of a case.

        Raises:
            CgError: If different sources are set for the samples linked to a case.
        """
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id=case_id)
        source_types: set[str | None] = {
            self.lims_api.get_source(sample_id) for sample_id in sample_ids
        }
        if len(source_types) > 1:
            raise CgError(f"Different source types found for case: {case_id} ({source_types})")
        return source_types.pop()
