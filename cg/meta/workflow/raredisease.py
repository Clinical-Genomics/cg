"""Module for Raredisease Analysis API."""

import logging
from typing import Any

from cg.constants import Pipeline
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.raredisease.raredisease import RarediseaseSampleSheetEntry, RarediseaseParameters
from cg.store.models import Case, Sample

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
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(case_id=case_id)
        pipeline_parameters: RarediseaseParameters = self.get_pipeline_parameters(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RarediseaseSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters.dict())

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, case: Case = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_name: str = sample.name
        sample_metadata: list[str] = self.gather_file_metadata_for_sample(sample)
        lane: str = "get lane info from somewhere"
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        sex: str = sample.sex
        phenotype: str = "get from sample/case links: status"
        paternal_id: str = "get from relationships"
        maternal_id: str = "get from relationships"
        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=sample_name,
            lane=lane,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=sex,
            phenotype=phenotype,
            paternal_id=paternal_id,
            maternal_id=maternal_id,
            case_id=case,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_sample_sheet_content(
        self,
        case_id: str,
    ) -> list[list[Any]]:
        """Write sample sheet for Raredisease analysis in case folder."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content = []
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        LOG.debug("Getting sample sheet information")
        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(sample=link.sample, case=case)
            )
        return sample_sheet_content

    def get_pipeline_parameters(self, case_id: str) -> RarediseaseParameters:
        """Return Raredisease parameters."""
        LOG.debug("Getting parameters information")
        return RarediseaseParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            sample_sheet_path=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            priority=self.account,
        )
