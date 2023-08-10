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
    TaxprofilerDefaults,
)
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.nf_handlers import NfBaseHandler
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler_sample import TaxprofilerSample
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
        fastq_r1: List[str],
        fastq_r2: List[str],
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
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

    @staticmethod
    def write_samplesheet_csv(
        samplesheet_content: Dict[str, List[str]],
        headers: List[str],
        config_path: Path,
    ) -> None:
        """Write sample sheet CSV file."""
        with open(config_path, "w") as outfile:
            outfile.write(",".join(headers))
            for i in range(len(samplesheet_content[NFX_SAMPLE_HEADER])):
                outfile.write("\n")
                outfile.write(",".join([samplesheet_content[k][i] for k in headers]))

    def write_sample_sheet(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
        dry_run: bool = False,
    ) -> None:
        """Write sample sheet for taxprofiler analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: Dict[str, List[str]] = {}

        for link in case.links:
            sample_name: str = link.sample.name
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = self.extract_read_files(
                metadata=sample_metadata, forward_read=True
            )
            fastq_r2: List[str] = self.extract_read_files(
                metadata=sample_metadata, reverse_read=True
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
            if dry_run:
                continue
            self.write_samplesheet_csv(
                samplesheet_content=sample_sheet_content,
                headers=TAXPROFILER_SAMPLE_SHEET_HEADERS,
                config_path=self.get_case_config_path(case_id=case_id),
            )

    def write_params_file(self, case_id: str, dry_run: bool = False) -> None:
        """Write params-file for taxprofiler analysis in case folder."""
        default_options: Dict[str, str] = self.get_default_parameters(case_id=case_id)
        NfBaseHandler.write_nextflow_yaml(
            content=default_options,
            file_path=self.get_params_file_path(case_id=case_id),
        )

    def get_default_parameters(self, case_id: str) -> Dict:
        """Returns a dictionary with default Taxprofiler parameters."""
        return {
            "input": self.get_case_config_path(case_id=case_id).as_posix(),
            "databases": self.databases,
            "outdir": self.get_case_path(case_id=case_id).as_posix(),
            "save_preprocessed_reads": TaxprofilerDefaults.SAVE_PREPROCESSED_READS,
            "perform_shortread_qc": TaxprofilerDefaults.PERFORM_SHORTREAD_QC,
            "perform_shortread_complexityfilter": TaxprofilerDefaults.PERFORM_SHORTREAD_COMPLEXITYFILTER,
            "save_complexityfiltered_reads": TaxprofilerDefaults.SAVE_COMPLEXITYFILTERED_READS,
            "perform_shortread_hostremoval": TaxprofilerDefaults.PERFORM_SHORTREAD_HOSTREMOVAL,
            "hostremoval_reference": self.hostremoval_reference,
            "save_hostremoval_index": TaxprofilerDefaults.SAVE_HOSTREMOVAL_INDEX,
            "save_hostremoval_mapped": TaxprofilerDefaults.SAVE_HOSTREMOVAL_MAPPED,
            "save_hostremoval_unmapped": TaxprofilerDefaults.SAVE_HOSTREMOVAL_UNMAPPED,
            "perform_runmerging": TaxprofilerDefaults.PERFORM_RUNMERGING,
            "run_kraken2": TaxprofilerDefaults.RUN_KRAKEN2,
            "kraken2_save_reads": TaxprofilerDefaults.KRAKEN2_SAVE_READS,
            "kraken2_save_readclassification": TaxprofilerDefaults.KRAKEN2_SAVE_READCLASSIFICATION,
            "run_krona": TaxprofilerDefaults.RUN_KRONA,
            "run_profile_standardisation": TaxprofilerDefaults.RUN_PROFILE_STANDARDISATION,
            "priority": self.account,
            "clusterOptions": f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
        }

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
        self.write_sample_sheet(
            case_id=case_id, instrument_platform=instrument_platform, fasta=fasta, dry_run=dry_run
        )
        LOG.info("Sample sheet written")
        LOG.info("Generating parameters file")
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_params_file(case_id=case_id, dry_run=dry_run)

        LOG.info("Configs files written")
