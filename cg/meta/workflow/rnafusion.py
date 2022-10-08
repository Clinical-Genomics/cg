"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import List
import pandas as pd
import csv

from cg.constants import Pipeline
from cg.constants.constants import (
    RNAFUSION_SAMPLESHEET_HEADERS,
    NFX_SAMPLE_HEADER,
    NFX_READ1_HEADER,
    NFX_READ2_HEADER,
    RNAFUSION_STRANDEDNESS_HEADER,
)

from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.meta.workflow.fastq import RnafusionFastqHandler
from cg.models.cg_config import CGConfig
from cg.models.rnafusion.rnafusion_sample import RnafusionSample
from cg.models.nextflow.deliverable import NextflowDeliverable, replace_dict_values
from cg.utils import Process
from cg import resources
from pydantic import ValidationError
from subprocess import CalledProcessError


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

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return RnafusionFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(self.config.rnafusion.binary_path, "", "", self.conda_env)
        return self._process

    def get_profile(self, profile: str = None) -> str:
        if profile:
            return profile
        return self.profile

    @staticmethod
    def build_samplesheet_content(
        case_id: str, fastq_r1: list, fastq_r2: list, strandedness: str
    ) -> dict:
        """Build samplesheet headers and lists"""
        try:
            RnafusionSample(
                sample=case_id, fastq_r1=fastq_r1, fastq_r2=fastq_r2, strandedness=strandedness
            )
        except ValidationError as e:
            LOG.error(e)
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
            raise NotImplementedError("Case objects are assuming one link")

        for link in case_obj.links:
            sample_metadata: list = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: list = NextflowAnalysisAPI.extract_read_files(1, sample_metadata)
            fastq_r2: list = NextflowAnalysisAPI.extract_read_files(2, sample_metadata)
            samplesheet_content: dict = self.build_samplesheet_content(
                case_id, fastq_r1, fastq_r2, strandedness
            )
            LOG.info(samplesheet_content)
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content,
                RNAFUSION_SAMPLESHEET_HEADERS,
                NextflowAnalysisAPI.get_case_config_path(case_id, self.root_dir),
            )

    def get_references_path(self, genomes_bases: Path = None) -> Path:
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
    ) -> dict:
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

    def get_pipeline_version(self, case_id: str) -> str:
        try:
            self.process.run_command(["-version"])
            return list(self.process.stdout_lines())[2].split()[1]
        except (Exception, CalledProcessError):
            LOG.warning("Could not retrieve %s workflow version!", self.pipeline)
            return "0.0.0"

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
        options = self.__build_command_str(
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
        nextflow_options = self.__build_command_str(
            NextflowAnalysisAPI.get_verified_arguments_nextflow(
                case_id=case_id, log=log, pipeline=self.pipeline, root_dir=self.root_dir
            )
        )
        command = ["run", self.nfcore_pipeline_path]
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

    def verify_case_config_file_exists(self, case_id: str):
        NextflowAnalysisAPI.verify_case_config_file_exists(case_id=case_id, root_dir=self.root_dir)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        LOG.info("Reaching here C")
        LOG.info(
            NextflowAnalysisAPI.get_deliverables_file_path(case_id=case_id, root_dir=self.root_dir)
        )
        return NextflowAnalysisAPI.get_deliverables_file_path(
            case_id=case_id, root_dir=self.root_dir
        )

    def verify_deliverables_file_exists(self, case_id: str):
        NextflowAnalysisAPI.verify_deliverables_file_exists(case_id=case_id, root_dir=self.root_dir)

    # def replace_in_dataframe(self, dataframe: pd.DataFrame, replace_map: dict) -> pd.DataFrame:
    #     for str_to_replace, with_value in replace_map.items():
    #         dataframe = dataframe.replace(str_to_replace, with_value, regex=True)
    #     return dataframe

    # def parse_template_deliverables_file(
    #     self, case_id: str, deliverables_template: pd.DataFrame
    # ) -> pd.DataFrame:
    #     """Replace PATHTOCASE and CASEID from template deliverables file
    #     to corresponding strings, add path_index column."""
    #     replace_map: dict = {
    #         "PATHTOCASE": str(NextflowAnalysisAPI.get_case_path(case_id, self.root_dir)),
    #         "CASEID": case_id,
    #     }
    #
    #     deliverables_template = self.replace_in_dataframe(deliverables_template, replace_map)
    #
    #     deliverables_template["path_index"] = "~"
    #     return deliverables_template

    # def convert_deliverables_dataframe(self, dataframe: pd.DataFrame) -> dict:
    #     """Convert deliverables dataframe."""
    #     return dataframe.to_dict(orient="records").replace("'~'", "~")

    def report_deliver(self, case_id: str) -> None:
        """Get a deliverables file template from resources, parse it and, then write the deliverables file."""
        deliverables_content: dict = NextflowAnalysisAPI.get_template_deliverables_file_content(
            resources.rnafusion_bundle_filenames_path
        )
        try:
            for index, deliver_file in enumerate(deliverables_content):
                NextflowDeliverable(deliverables=deliver_file)
                deliverables_content[index] = replace_dict_values(
                    NextflowAnalysisAPI.get_replace_map(case_id=case_id, root_dir=self.root_dir),
                    deliver_file,
                )
        except ValidationError as e:
            LOG.error(e)
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
