"""Module for Taxprofiler Analysis API."""

import logging
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError
from cg.constants import Pipeline
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

    def get_samples(self, case_id: str) -> List[Sample]:
        case_id: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        return [link.sample_id for link in case_id.links]

    def get_fastq_files(self, case_id: str) -> None:
        case_id = self.status_db.get_case_by_internal_id(internal_id=case_id)
        for link in case_id.links:
            self.link_fastq_files_for_sample(
                case_id=case_id,
                sample_id=link.sample,
            )

    @staticmethod
    def build_sample_sheet_content(
        case_id: str,
        sample_id: str,
        fastq_r1: List[str],
        fastq_r2: List[str],
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str] = "",
    ) -> Dict[str, List[str]]:
        """Build sample sheet headers and lists."""
        try:
            TaxprofilerSample(
                # sample=case_id,
                sample=sample_id,
                fastq_r1=fastq_r1,
                fastq_r2=fastq_r2,
                instrument_platform=instrument_platform,
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        # Create a dictionary to store the sample sheet content
        sample_sheet_content: Dict[str, List[str]] = {
            NFX_SAMPLE_HEADER: [],
            TAXPROFILER_RUN_ACCESSION: [],
            TAXPROFILER_INSTRUMENT_PLATFORM: [],
            NFX_READ1_HEADER: [],
            NFX_READ2_HEADER: [],
            TAXPROFILER_FASTA_HEADER: [],
        }

        # Loop through the fastq files and add values for each sample
        for r1, r2 in zip(fastq_r1, fastq_r2):
            # Create a new sample ID for each iteration
            sample_ids: List[str] = [sample_id]
            sample_sheet_content[NFX_SAMPLE_HEADER].extend(sample_ids)
            sample_sheet_content[TAXPROFILER_RUN_ACCESSION].extend(sample_ids)
            sample_sheet_content[TAXPROFILER_INSTRUMENT_PLATFORM].append(instrument_platform)
            sample_sheet_content[NFX_READ1_HEADER].append(r1)
            sample_sheet_content[NFX_READ2_HEADER].append(r2)
            sample_sheet_content[TAXPROFILER_FASTA_HEADER].append(fasta)

        return sample_sheet_content

    def write_sample_sheet(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str],
    ) -> None:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)

        for link in case.links:
            sample_id: str = link.sample.internal_id
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = NextflowAnalysisAPI.extract_read_files(1, sample_metadata)
            fastq_r2: List[str] = NextflowAnalysisAPI.extract_read_files(2, sample_metadata)
            sample_sheet_content: Dict[str, List[str]] = self.build_sample_sheet_content(
                case_id=case_id,
                sample_id=sample_id,
                fastq_r1=fastq_r1,
                fastq_r2=fastq_r2,
                instrument_platform=instrument_platform,
                fasta=fasta,
            )
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
