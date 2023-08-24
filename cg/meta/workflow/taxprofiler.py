"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from pydantic.v1 import ValidationError

from cg.constants import Pipeline
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.sequencing import SequencingPlatform
from cg.constants.taxprofiler import (
    TAXPROFILER_FASTA_HEADER,
    TAXPROFILER_INSTRUMENT_PLATFORM,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_SAMPLE_SHEET_HEADERS,
)
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import PipelineParameters
from cg.models.taxprofiler.taxprofiler import TaxprofilerParameters, TaxprofilerSample
from cg.store.models import Family, Sample

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

    @property
    def sample_sheet_header(self) -> List[str]:
        """Return sample sheet headers."""
        return TaxprofilerSample.headers()

    @staticmethod
    def reformat_sample_content(sample_sheet: TaxprofilerSample) -> List[List[str]]:
        """Reformat sample sheet content as a list of list, where each list represents a line in the final file."""
        return [
            [
                sample_sheet.sample,
                sample_sheet.run_accession,
                sample_sheet.instrument_platform,
                fastq_forward,
                fastq_reverse,
                sample_sheet.fasta,
            ]
            for fastq_forward, fastq_reverse in zip(
                sample_sheet.fastq_forward, sample_sheet.fastq_reverse
            )
        ]

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, instrument_platform: SequencingPlatform.ILLUMINA, fasta: str = ""
    ) -> List[List[str]]:
        """Get sample sheet information per sample."""
        sample_name: str = sample.name
        sample_metadata: List[str] = self.gather_file_metadata_for_sample(sample)
        forward_read: List[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        reverse_read: List[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        sample_sheet = TaxprofilerSample(
            sample=sample_name,
            run_accession=sample_name,
            instrument_platform=instrument_platform,
            fastq_forward=forward_read,
            fastq_reverse=reverse_read,
            fasta=fasta,
        )
        return self.reformat_sample_content(sample_sheet=sample_sheet)

    def get_sample_sheet_content(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
    ) -> List[List[Any]]:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: List = []
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        LOG.info("Getting sample sheet information")
        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(
                    sample=link.sample, instrument_platform=instrument_platform, fasta=fasta
                )
            )
        return sample_sheet_content

    def get_pipeline_parameters(self, case_id: str) -> PipelineParameters:
        """Return Taxprofiler parameters."""
        LOG.info("Getting parameters information")
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
        """Create sample sheet file and parameters file for Taxprofiler analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: List[List[Any]] = self.get_sample_sheet_content(
            case_id=case_id,
            instrument_platform=instrument_platform,
            fasta=fasta,
        )
        pipeline_parameters: dict = self.get_pipeline_parameters(case_id=case_id).dict()
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_case_config_path(case_id=case_id),
            header=self.sample_sheet_header,
        )
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters)
