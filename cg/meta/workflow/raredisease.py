"""Module for Raredisease Analysis API."""

import logging

from cg.constants import Pipeline
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RAREDISEASE,
    ):
        super().__init__(config=config, pipeline=pipeline)

    def config_case(
        self,
        case_id: str,
        dry_run: bool,
    ) -> None:
        """Create config files (parameters and sample sheet) for Raredisease analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(
            case_id=case_id, strandedness=strandedness
        )
        pipeline_parameters: RarediseaseParameters = self.get_pipeline_parameters(
            case_id=case_id, genomes_base=genomes_base
        )
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RarediseaseSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters.dict())
