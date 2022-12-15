"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from cg import resources
from cg.constants import Pipeline
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.rnafusion import RNAFUSION_SAMPLESHEET_HEADERS, RNAFUSION_STRANDEDNESS_HEADER
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import RnafusionFastqHandler
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nextflow.deliverables import NextflowDeliverables, replace_dict_values
from cg.models.rnafusion.rnafusion_sample import RnafusionSample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class RnafusionAnalysisAPI(AnalysisAPI):
    """Handles communication between RNAFUSION processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RNAFUSION,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.rnafusion.root
        self.nfcore_pipeline_path: str = config.rnafusion.pipeline_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return RnafusionFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.config.rnafusion.binary_path,
                environment=self.conda_env,
                conda_binary=self.conda_binary,
            )
        return self._process

    def get_profile(self, profile: Optional[str] = None) -> str:
        if profile:
            return profile
        return self.profile

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    def verify_analysis_finished(self, case_id):
        return NextflowAnalysisAPI.verify_analysis_finished(case_id=case_id, root_dir=self.root_dir)

    @staticmethod
    def build_samplesheet_content(
        case_id: str, fastq_r1: List[str], fastq_r2: List[str], strandedness: str
    ) -> Dict[str, List[str]]:
        """Build samplesheet headers and lists"""
        try:
            RnafusionSample(
                sample=case_id, fastq_r1=fastq_r1, fastq_r2=fastq_r2, strandedness=strandedness
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        samples_full_list: list = []
        strandedness_full_list: list = []
        # Complete sample and strandedness lists to the same length as fastq_r1:
        for _ in range(len(fastq_r1)):
            samples_full_list.append(case_id)
            strandedness_full_list.append(strandedness)

        samplesheet_content: dict = {
            NFX_SAMPLE_HEADER: samples_full_list,
            NFX_READ1_HEADER: fastq_r1,
            NFX_READ2_HEADER: fastq_r2,
            RNAFUSION_STRANDEDNESS_HEADER: strandedness_full_list,
        }
        return samplesheet_content

    def write_samplesheet(self, case_id: str, strandedness: str) -> None:
        """Write sample sheet for rnafusion analysis in case folder."""
        case_obj = self.status_db.family(case_id)
        if len(case_obj.links) != 1:
            raise NotImplementedError(
                "Case objects are assumed to be related to a single sample (one link)"
            )

        for link in case_obj.links:
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = NextflowAnalysisAPI.extract_read_files(1, sample_metadata)
            fastq_r2: List[str] = NextflowAnalysisAPI.extract_read_files(2, sample_metadata)
            samplesheet_content: Dict[str, List[str]] = self.build_samplesheet_content(
                case_id, fastq_r1, fastq_r2, strandedness
            )
            LOG.info(samplesheet_content)
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content,
                RNAFUSION_SAMPLESHEET_HEADERS,
                NextflowAnalysisAPI.get_case_config_path(case_id, self.root_dir),
            )

    def get_references_path(self, genomes_bases: Optional[Path] = None) -> Path:
        if genomes_bases:
            return genomes_bases
        return Path(self.references)

    def get_verified_arguments(
        self,
        case_id: str,
        work_dir: Path,
        resume: bool,
        profile: str,
        with_tower: bool,
        stub: bool,
        input: Path,
        outdir: Path,
        genomes_base: Path,
        trim: bool,
        fusioninspector_filter: bool,
        all: bool,
        pizzly: bool,
        squid: bool,
        starfusion: bool,
        fusioncatcher: bool,
        arriba: bool,
    ) -> Dict[str, str]:
        """Transforms click argument related to rnafusion that were left empty into
        defaults constructed with case_id paths or from config."""
        return {
            "-w": NextflowAnalysisAPI.get_workdir_path(case_id, self.root_dir, work_dir),
            "-resume": resume,
            "-profile": self.get_profile(profile=profile),
            "-with-tower": with_tower,
            "-stub": stub,
            "--input": NextflowAnalysisAPI.get_input_path(case_id, self.root_dir, input),
            "--outdir": NextflowAnalysisAPI.get_outdir_path(case_id, self.root_dir, outdir),
            "--genomes_base": self.get_references_path(genomes_base),
            "--trim": trim,
            "--fusioninspector_filter": fusioninspector_filter,
            "--all": all,
            "--pizzly": pizzly,
            "--squid": squid,
            "--starfusion": starfusion,
            "--fusioncatcher": fusioncatcher,
            "--arriba": arriba,
        }

    @staticmethod
    def __build_command_str(options: dict) -> List[str]:
        formatted_options: list = []
        for key, val in options.items():
            if val:
                formatted_options.append(str(key))
                formatted_options.append(str(val))
        return formatted_options

    def config_case(
        self,
        case_id: str,
        strandedness: str,
    ) -> None:
        """Create sample sheet file for RNAFUSION analysis."""
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        self.write_samplesheet(case_id, strandedness)
        LOG.info("Samplesheet written")

    def run_analysis(
        self,
        case_id: str,
        log: Path,
        work_dir: Path,
        resume: bool,
        profile: str,
        with_tower: bool,
        stub: bool,
        input: Path,
        outdir: Path,
        genomes_base: Path,
        trim: bool,
        fusioninspector_filter: bool,
        all: bool,
        pizzly: bool,
        squid: bool,
        starfusion: bool,
        fusioncatcher: bool,
        arriba: bool,
        dry_run: bool = False,
    ) -> None:
        """Execute RNAFUSION run analysis with given options."""
        options: List[str] = self.__build_command_str(
            self.get_verified_arguments(
                case_id=case_id,
                work_dir=work_dir,
                resume=resume,
                profile=profile,
                with_tower=with_tower,
                stub=stub,
                input=input,
                outdir=outdir,
                genomes_base=genomes_base,
                trim=trim,
                fusioninspector_filter=fusioninspector_filter,
                all=all,
                pizzly=pizzly,
                squid=squid,
                starfusion=starfusion,
                fusioncatcher=fusioncatcher,
                arriba=arriba,
            )
        )
        nextflow_options: List[str] = self.__build_command_str(
            NextflowAnalysisAPI.get_verified_arguments_nextflow(
                case_id=case_id, pipeline=self.pipeline, root_dir=self.root_dir, log=log
            )
        )
        command: List[str] = ["run", self.nfcore_pipeline_path]
        parameters = (
            nextflow_options
            + ["-bg", "-q"]
            + command
            + options
            + NextflowAnalysisAPI.get_nextflow_stdout_stderr(
                case_id=case_id, root_dir=self.root_dir
            )
        )
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def verify_case_config_file_exists(self, case_id: str) -> None:
        NextflowAnalysisAPI.verify_case_config_file_exists(case_id=case_id, root_dir=self.root_dir)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        return NextflowAnalysisAPI.get_deliverables_file_path(
            case_id=case_id, root_dir=self.root_dir
        )

    def get_pipeline_version(self, case_id: str) -> str:
        return NextflowAnalysisAPI.get_pipeline_version(
            case_id=case_id, root_dir=self.root_dir, pipeline=self.pipeline
        )

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        NextflowAnalysisAPI.verify_deliverables_file_exists(case_id=case_id, root_dir=self.root_dir)

    def report_deliver(self, case_id: str) -> None:
        """Get a deliverables file template from resources, parse it and, then write the deliverables file."""
        deliverables_content: dict = NextflowAnalysisAPI.get_template_deliverables_file_content(
            resources.rnafusion_bundle_filenames_path
        )
        try:
            for index, deliver_file in enumerate(deliverables_content):
                NextflowDeliverables(deliverables=deliver_file)
                deliverables_content[index] = replace_dict_values(
                    NextflowAnalysisAPI.get_replace_map(case_id=case_id, root_dir=self.root_dir),
                    deliver_file,
                )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        NextflowAnalysisAPI.write_deliverables_bundle(
            deliverables_content=NextflowAnalysisAPI.add_bundle_header(
                deliverables_content=deliverables_content
            ),
            file_path=NextflowAnalysisAPI.get_deliverables_file_path(
                case_id=case_id, root_dir=self.root_dir
            ),
        )
        LOG.info(
            "Writing deliverables file in "
            + str(
                NextflowAnalysisAPI.get_deliverables_file_path(
                    case_id=case_id, root_dir=self.root_dir
                )
            )
        )
