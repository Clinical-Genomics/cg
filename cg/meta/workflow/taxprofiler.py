"""Module for Taxprofiler Analysis API."""

import logging
from typing import Dict, List, Optional

from pydantic.v1 import ValidationError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.constants import Pipeline
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.sequencing import SequencingPlatform
from cg.constants.taxprofiler import (
    TAXPROFILER_INSTRUMENT_PLATFORM,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_SAMPLE_SHEET_HEADERS,
    TAXPROFILER_FASTA_HEADER,
)
from cg.meta.workflow.fastq import TaxprofilerFastqHandler
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.models.taxprofiler.taxprofiler_sample import TaxprofilerSample
from cg.store.models import Family, Sample

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(AnalysisAPI):
    """Handles communication between Taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.TAXPROFILER,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.taxprofiler.root

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return TaxprofilerFastqHandler

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    @staticmethod
    def build_sample_sheet_content(
        sample_name: str,
        fastq_r1: List[str],
        fastq_r2: List[str],
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str] = "",
    ) -> Dict[str, List[str]]:
        """Build sample sheet headers and lists."""
        try:
            TaxprofilerSample(
                sample=sample_name,
                fastq_r1=fastq_r1,
                fastq_r2=fastq_r2,
                instrument_platform=instrument_platform,
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        # Complete sample lists to the same length as fastq_r1:
        samples_full_list: List[str] = [sample_name] * len(fastq_r1)
        instrument_full_list: List[str] = [instrument_platform] * len(fastq_r1)
        fasta_full_list: List[str] = [fasta] * len(fastq_r1)

        sample_sheet_content: Dict[str, List[str]] = {
            NFX_SAMPLE_HEADER: samples_full_list,
            TAXPROFILER_RUN_ACCESSION: samples_full_list,
            TAXPROFILER_INSTRUMENT_PLATFORM: instrument_full_list,
            NFX_READ1_HEADER: fastq_r1,
            NFX_READ2_HEADER: fastq_r2,
            TAXPROFILER_FASTA_HEADER: fasta_full_list,
        }

        return sample_sheet_content

    def write_sample_sheet(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str],
    ) -> None:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: Dict[str, List[str]] = {}

        for link in case.links:
            sample_name: str = link.sample.name
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = NextflowAnalysisAPI.extract_read_files(
                read_nb=1, metadata=sample_metadata
            )
            fastq_r2: List[str] = NextflowAnalysisAPI.extract_read_files(
                read_nb=2, metadata=sample_metadata
            )
            sample_content: Dict[str, List[str]] = self.build_sample_sheet_content(
                sample_name=sample_name,
                fastq_r1=fastq_r1,
                fastq_r2=fastq_r2,
                instrument_platform=instrument_platform,
                fasta=fasta,
            )

            for headers, contents in sample_content.items():
                sample_sheet_content.setdefault(headers, []).extend(contents)

            LOG.info(sample_sheet_content)
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content=sample_sheet_content,
                headers=TAXPROFILER_SAMPLE_SHEET_HEADERS,
                config_path=NextflowAnalysisAPI.get_case_config_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )

    def config_case(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str],
    ) -> None:
        """Create sample sheet file for Taxprofiler analysis."""
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        LOG.info("Generating sample sheet")
        self.write_sample_sheet(
            case_id=case_id,
            instrument_platform=instrument_platform,
            fasta=fasta,
        )
        LOG.info("Sample sheet written")
