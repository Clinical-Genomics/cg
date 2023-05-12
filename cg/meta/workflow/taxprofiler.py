"""Module for Taxprofiler Analysis API."""

import logging
from typing import Dict, List, Optional

from pydantic import ValidationError
from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.constants import Pipeline
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.taxprofiler import (
    TAXPROFILER_INSTRUMENT_PLATFORM,
    TAXPROFILER_RUN_ACCESSION,
    TAXPROFILER_SAMPLESHEET_HEADERS,
    TAXPROFILER_ACCEPTED_PLATFORMS,
    TaxprofilerDefaults,
)
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.models.taxprofiler.taxprofiler_sample import TaxprofilerSample

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
        self.root_dir = config.taxprofiler.root

    @property
    def root(self) -> str:
        return self.root_dir

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    @staticmethod
    def build_samplesheet_content(
        case_id: str, fastq_r1: List[str], fastq_r2: List[str]
    ) -> Dict[str, List[str]]:
        """Build samplesheet headers and lists"""
        try:
            TaxprofilerSample(
                sample=case_id,
                fastq_r1=fastq_r1,
                fastq_r2=fastq_r2,
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        samples_full_list: list = []
        # Complete sample lists to the same length as fastq_r1:
        for _ in range(len(fastq_r1)):
            samples_full_list.append(case_id)

        samplesheet_content: dict = {
            NFX_SAMPLE_HEADER: samples_full_list,
            TAXPROFILER_RUN_ACCESSION: samples_full_list,
            TAXPROFILER_INSTRUMENT_PLATFORM: TAXPROFILER_INSTRUMENT_PLATFORM,
            NFX_READ1_HEADER: fastq_r1,
            NFX_READ2_HEADER: fastq_r2,
        }
        return samplesheet_content

    def write_samplesheet(self, case_id: str) -> None:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case_obj = self.status_db.get_case_by_internal_id(internal_id=case_id)
        for link in case_obj.links:
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = NextflowAnalysisAPI.extract_read_files(1, sample_metadata)
            fastq_r2: List[str] = NextflowAnalysisAPI.extract_read_files(2, sample_metadata)
            samplesheet_content: Dict[str, List[str]] = self.build_samplesheet_content(
                case_id, fastq_r1, fastq_r2
            )
            LOG.info(samplesheet_content)
            # if dry_run:
            #     continue
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content=samplesheet_content,
                headers=[str(header) for header in TAXPROFILER_SAMPLESHEET_HEADERS],
                config_path=NextflowAnalysisAPI.get_case_config_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )

    def config_case(self, case_id: str) -> None:
        """Create sample sheet file for Taxprofiler analysis."""
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        LOG.info("Generating samplesheet")
        self.write_samplesheet(case_id=case_id)
        # LOG.info("Samplesheet written")
