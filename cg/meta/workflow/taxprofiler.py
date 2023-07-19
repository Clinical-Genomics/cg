"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
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
    TaxprofilerDefaults,
)
from cg.meta.workflow.fastq import TaxprofilerFastqHandler
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.models.taxprofiler.taxprofiler_sample import TaxprofilerSample
from cg.utils import Process
from cg.store.models import Family, Sample
from cg.utils import Process

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
        self.nfcore_pipeline_path: str = config.taxprofiler.pipeline_path
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.profile: str = config.taxprofiler.profile
        self.revision: str = config.taxprofiler.revision
        self.hostremoval_reference: str = config.taxprofiler.hostremoval_reference
        self.databases: str = config.taxprofiler.databases
        self.account: str = config.taxprofiler.slurm.account
        self.email: str = config.taxprofiler.slurm.mail_user

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return TaxprofilerFastqHandler

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.tower_binary_path,
            )
        return self._process

    @process.setter
    def process(self, process: Process):
        self._process = process

    def get_profile(self, profile: Optional[str] = None) -> str:
        if profile:
            return profile
        return self.profile

    def get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return NextflowAnalysisAPI.get_case_path(case_id=case_id, root_dir=self.root)

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
        dry_run: bool = False,
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
            if dry_run:
                continue
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content=sample_sheet_content,
                headers=TAXPROFILER_SAMPLE_SHEET_HEADERS,
                config_path=NextflowAnalysisAPI.get_case_config_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )

    def write_params_file(self, case_id: str, dry_run: bool = False) -> None:
        """Write params-file for taxprofiler analysis in case folder."""
        default_options: Dict[str, str] = self.get_default_parameters(case_id=case_id)
        if dry_run:
            return
        NextflowAnalysisAPI.write_nextflow_yaml(
            content=default_options,
            file_path=NextflowAnalysisAPI.get_params_file_path(
                case_id=case_id, root_dir=self.root_dir
            ),
        )

    def get_reference_path(self) -> Path:
        return Path(self.hostremoval_reference).absolute()

    def get_database_samplesheet(self) -> Path:
        return Path(self.databases).absolute()

    def get_default_parameters(self, case_id: str) -> Dict:
        """Returns a dictionary with default Taxprofiler parameters."""
        return {
            "input": NextflowAnalysisAPI.get_input_path(
                case_id=case_id, root_dir=self.root_dir
            ).as_posix(),
            "databases": self.get_database_samplesheet().as_posix(),
            "outdir": NextflowAnalysisAPI.get_outdir_path(
                case_id=case_id, root_dir=self.root_dir
            ).as_posix(),
            "save_preprocessed_reads": TaxprofilerDefaults.SAVE_PREPROCESSED_READS,
            "perform_shortread_qc": TaxprofilerDefaults.PERFORM_SHORTREAD_QC,
            "perform_shortread_complexityfilter": TaxprofilerDefaults.PERFORM_SHORTREAD_COMPLEXITYFILTER,
            "save_complexityfiltered_reads": TaxprofilerDefaults.SAVE_COMPLEXITYFILTERED_READS,
            "perform_shortread_hostremoval": TaxprofilerDefaults.PERFORM_SHORTREAD_HOSTREMOVAL,
            "hostremoval_reference": self.get_reference_path().as_posix(),
            "save_hostremoval_index": TaxprofilerDefaults.SAVE_HOSTREMOVAL_INDEX,
            "save_hostremoval_mapped": TaxprofilerDefaults.SAVE_HOSTREMOVAL_MAPPED,
            "save_hostremoval_unmapped": TaxprofilerDefaults.SAVE_HOSTREMOVAL_UNMAPPED,
            "run_kraken2": TaxprofilerDefaults.RUN_KRAKEN2,
            "kraken2_save_reads": TaxprofilerDefaults.KRAKEN2_SAVE_READS,
            "kraken2_save_readclassification": TaxprofilerDefaults.KRAKEN2_SAVE_READCLASSIFICATION,
            "run_profile_standardisation": TaxprofilerDefaults.RUN_PROFILE_STANDARDISATION,
            "run_krona": TaxprofilerDefaults.RUN_KRONA,
            "priority": self.account,
            "clusterOptions": f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
        }

    def config_case(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: Optional[str],
        dry_run: bool,
    ) -> None:
        """Create sample sheet file for Taxprofiler analysis."""
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        LOG.info("Generating sample sheet")
        self.write_sample_sheet(
            case_id=case_id, instrument_platform=instrument_platform, fasta=fasta, dry_run=dry_run
        )
        LOG.info("Sample sheet written")
        LOG.info("Generating parameters file")
        self.write_params_file(case_id=case_id, dry_run=dry_run)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return

        LOG.info("Configs files written")

    def verify_case_config_file_exists(self, case_id: str, dry_run: bool = False) -> None:
        NextflowAnalysisAPI.verify_case_config_file_exists(
            case_id=case_id, root_dir=self.root_dir, dry_run=dry_run
        )

    def run_analysis(
        self, case_id: str, command_args: dict, use_nextflow: bool, dry_run: bool = False
    ) -> None:
        """Execute Taxprofiler run analysis with given options."""
        if use_nextflow:
            self.process = Process(
                binary=self.config.taxprofiler.binary_path,
                environment=self.conda_env,
                conda_binary=self.conda_binary,
                launch_directory=NextflowAnalysisAPI.get_case_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )
            LOG.info("Pipeline will be executed using nextflow")
            # parameters: List[str] = NextflowAnalysisAPI.get_nextflow_run_parameters(
            #    case_id=case_id,
            #    pipeline_path=self.nfcore_pipeline_path,
            #    root_dir=self.root_dir,
            #    command_args=command_args.dict(),
            # )
            # self.process.export_variables(
            #    export=NextflowAnalysisAPI.get_variables_to_export(
            #        case_id=case_id, root_dir=self.root_dir
            #    ),
            # )

            # command = self.process.get_command(parameters=parameters)
            # LOG.info(f"{command}")
            # sbatch_number: int = NextflowAnalysisAPI.execute_head_job(
            #    case_id=case_id,
            #    root_dir=self.root_dir,
            #    slurm_account=self.account,
            #    email=self.email,
            #    qos=self.get_slurm_qos_for_case(case_id=case_id),
            #    commands=command,
            #    dry_run=dry_run,
            # )
            # LOG.info(f"Nextflow head job running as job {sbatch_number}")

        else:
            LOG.info("Pipeline will be executed using tower")
