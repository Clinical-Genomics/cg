"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Dict, List
from pydantic.v1 import ValidationError
from cg.constants import Pipeline
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.sequencing import SequencingPlatform
from cg.constants.taxprofiler import (
    TAXPROFILER_INSTRUMENT_PLATFORM,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_SAMPLE_SHEET_HEADERS,
    TAXPROFILER_FASTA_HEADER,
)
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.nf_analysis import PipelineParameters
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler import TaxprofilerParameters, TaxprofilerSample
from cg.store.models import Family

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.TAXPROFILER,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.taxprofiler.root
        self.nfcore_pipeline_path: str = config.taxprofiler.pipeline_path
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.profile: str = config.taxprofiler.profile
        self.revision: str = config.taxprofiler.revision
        self.hostremoval_reference: Path = Path(config.taxprofiler.hostremoval_reference)
        self.databases: Path = Path(config.taxprofiler.databases)
        self.account: str = config.taxprofiler.slurm.account
        self.email: str = config.taxprofiler.slurm.mail_user
        self.nextflow_binary_path: str = config.taxprofiler.binary_path

    @staticmethod
    def build_sample_sheet_content(
        sample_name: str,
        fastq_forward: List[str],
        fastq_reverse: List[str],
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
    ) -> Dict[str, List[str]]:
        """Build sample sheet headers and lists."""
        try:
            TaxprofilerSample(
                sample=sample_name,
                fastq_forward=fastq_forward,
                fastq_reverse=fastq_reverse,
                instrument_platform=instrument_platform,
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        # Complete sample lists to the same length as fastq_forward:
        samples_full_list: List[str] = [sample_name] * len(fastq_forward)
        instrument_full_list: List[str] = [instrument_platform] * len(fastq_forward)
        fasta_full_list: List[str] = [fasta] * len(fastq_forward)

        sample_sheet_content: Dict[str, List[str]] = {
            NFX_SAMPLE_HEADER: samples_full_list,
            TAXPROFILER_RUN_ACCESSION: samples_full_list,
            TAXPROFILER_INSTRUMENT_PLATFORM: instrument_full_list,
            NFX_READ1_HEADER: fastq_forward,
            NFX_READ2_HEADER: fastq_reverse,
            TAXPROFILER_FASTA_HEADER: fasta_full_list,
        }

        return sample_sheet_content

    def write_sample_sheet(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
    ) -> None:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: Dict[str, List[str]] = {}

        for link in case.links:
            sample_name: str = link.sample.name
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_forward: List[str] = self.extract_read_files(
                metadata=sample_metadata, forward_read=True
            )
            fastq_reverse: List[str] = self.extract_read_files(
                metadata=sample_metadata, reverse_read=True
            )
            sample_content: Dict[str, List[str]] = self.build_sample_sheet_content(
                sample_name=sample_name,
                fastq_forward=fastq_forward,
                fastq_reverse=fastq_reverse,
                instrument_platform=instrument_platform,
                fasta=fasta,
            )

            for headers, contents in sample_content.items():
                sample_sheet_content.setdefault(headers, []).extend(contents)

            LOG.info(sample_sheet_content)
            self.write_sample_sheet_csv(
                samplesheet_content=sample_sheet_content,
                headers=TAXPROFILER_SAMPLE_SHEET_HEADERS,
                config_path=self.get_case_config_path(case_id=case_id),
            )

    def get_pipeline_parameters(self, case_id: str) -> PipelineParameters:
        """Return Taxprofiler parameters."""
        return TaxprofilerParameters(
            clusterOptions=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            input=self.get_case_config_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            databases=self.databases,
            hostremoval_reference=self.hostremoval_reference,
            priority=self.account,
        )

    def config_case(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        dry_run: bool,
        fasta: str = "",
    ) -> None:
        """Create sample sheet file for Taxprofiler analysis."""
        self.create_case_directory(case_id=case_id)
        LOG.info("Generating sample sheet")
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            case_id=case_id,
            instrument_platform=instrument_platform,
            fasta=fasta,
        )
        LOG.info("Generating parameters file")
        self.write_params_file(
            case_id=case_id,
            pipeline_parameters=self.get_pipeline_parameters(case_id=case_id).dict(),
        )

        LOG.info("Configs files written")
