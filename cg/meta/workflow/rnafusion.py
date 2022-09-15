"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import List
import pandas as pd
import os
import operator
import csv

from cg.io.controller import WriteFile
from pydantic import ValidationError
from cg.constants import DataDelivery, Pipeline
from cg.constants.constants import CaseActions
from cg.constants.constants import (
    STRANDEDNESS_DEFAULT,
    NFX_WORK_DIR,
    RNAFUSION_SAMPLESHEET_HEADERS,
    NFX_SAMPLE_HEADER,
    NFX_READ1_HEADER,
    NFX_READ2_HEADER,
    RNAFUSION_STRANDEDNESS_HEADER,
)

from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import RnafusionFastqHandler
from cg.models.cg_config import CGConfig
from cg.utils import Process
from cg import resources
from datetime import datetime
from subprocess import CalledProcessError
from cg.constants.constants import FileFormat


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

    def get_case_path(self, case_id: str) -> Path:
        """Returns a path where the rnafusion case should be located."""
        return Path(self.root_dir, case_id)

    def get_case_config_path(self, case_id: str) -> Path:
        """Generates a path where the Rnafusion sample sheet for the case_id should be located."""
        return Path((self.get_case_path(case_id)), case_id + "_samplesheet.csv")

    def make_case_folder(self, case_id: str) -> None:
        """Make the case folder where analysis should be located."""
        os.makedirs(self.get_case_path(case_id), exist_ok=True)

    def extract_read_files(self, read_nb: int, metadata: list) -> list:
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_nb]

    def build_samplesheet_content(
        self, case_id: str, fastq_r1: list, fastq_r2: list, strandedness: str
    ) -> dict:
        """Build samplesheet headers and lists"""
        samples_full_list: list = []
        strandedness_full_list: list = []
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

    def create_samplesheet_csv(self, samplesheet_content: dict, config_path: Path) -> None:
        """Write samplesheet csv file."""
        with open(config_path, "w") as outfile:
            outfile.write(",".join((RNAFUSION_SAMPLESHEET_HEADERS)))
            for i in range(len(samplesheet_content[NFX_SAMPLE_HEADER])):
                outfile.write("\n")
                outfile.write(
                    ",".join([samplesheet_content[k][i] for k in RNAFUSION_SAMPLESHEET_HEADERS])
                )

    def write_samplesheet(self, case_id: str, strandedness: str = STRANDEDNESS_DEFAULT) -> None:
        """Write sample sheet for rnafusion analysis in case folder."""
        case_obj = self.status_db.family(case_id)
        for link in case_obj.links:
            sample_metadata: list = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: list = self.extract_read_files(1, sample_metadata)
            fastq_r2: list = self.extract_read_files(2, sample_metadata)
            samplesheet_content: dict = self.build_samplesheet_content(
                case_id, fastq_r1, fastq_r2, strandedness
            )
            LOG.info(samplesheet_content)
            self.create_samplesheet_csv(samplesheet_content, self.get_case_config_path(case_id))

    def get_log_path(self, case_id: str, log: Path = None) -> Path:
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            self.get_case_path(case_id), case_id + "rnafusion_nextflow_log_" + launch_time + ".log"
        )

    def get_profile(self, profile: str = None) -> str:
        if profile:
            return profile
        return self.profile

    def get_workdir_path(self, case_id: str, work_dir: Path = None) -> Path:
        if work_dir:
            return work_dir
        return Path(self.get_case_path(case_id), NFX_WORK_DIR)

    def get_input_path(self, case_id: str, input: Path = None) -> Path:
        if input:
            return input
        return Path(self.get_case_config_path(case_id))

    def get_outdir_path(self, case_id: str, outdir: Path = None) -> Path:
        if outdir:
            return outdir
        return Path(self.get_case_path(case_id))

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
            "-w": self.get_workdir_path(case_id, work_dir),
            "-resume": resume,
            "-profile": self.get_profile(profile),
            "-with-tower": with_tower,
            "-stub": stub,
            "--input": self.get_input_path(case_id, input),
            "--outdir": self.get_outdir_path(case_id, outdir),
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

    def get_verified_arguments_nextflow(
        self,
        case_id: str,
        log: Path,
    ) -> dict:
        """Transforms click argument related to nextflow that were left empty
        into defaults constructed with case_id paths."""

        return {
            "-log": self.get_log_path(case_id, log),
        }

    def get_pipeline_version(self, case_id: str) -> str:
        try:
            self.process.run_command(["-version"])
            return list(self.process.stdout_lines())[2].split()[1]
        except (Exception, CalledProcessError):
            LOG.warning("Could not retrieve %s workflow version!", self.pipeline)
            return "0.0.0"

    def get_nextflow_stdout_stderr(self, case_id: str) -> List[str]:
        return [
            " > "
            + str(self.get_case_path(case_id))
            + "/"
            + case_id
            + "-stdout.log 2> "
            + str(self.get_case_path(case_id))
            + "/"
            + case_id
            + "-stdout.err  < /dev/null & "
        ]

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
        self.make_case_folder(case_id)
        if not (self.get_case_config_path(case_id)).is_file():
            LOG.info("Samplesheet does not exist, writing samplesheet")
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
            self.get_verified_arguments_nextflow(
                case_id=case_id,
                log=log,
            )
        )
        command = ["run", self.nfcore_pipeline_path]
        parameters = (
            nextflow_options
            + ["-bg", "-q"]
            + command
            + options
            + self.get_nextflow_stdout_stderr(case_id)
        )
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the rnafusion deliverables file for the case_id should be located.

        (Optional) Checks if deliverables file exists.
        """
        return Path(self.get_case_path(case_id), case_id + "_deliverables.yaml")

    def get_template_deliverables_file_content(
        self, rnafusion_bundle_template: Path
    ) -> pd.DataFrame:
        """Read deliverables file template and return content."""
        return pd.read_csv(rnafusion_bundle_template)

    def replace_in_dataframe(self, dataframe: pd.DataFrame, replace_map: dict) -> pd.DataFrame:
        for str_to_replace, with_value in replace_map.item():
            dataframe = dataframe.replace(str_to_replace, with_value, regex=True)

    def parse_template_deliverables_file(
        self, case_id: str, deliverables_template: pd.DataFrame
    ) -> pd.DataFrame:
        """Replace PATHTOCASE and CASEID from template deliverables file
        to corresponding strings, add path_index column."""
        replace_map: dict[str, str] = {
            "PATHTOCASE": str(self.get_case_path(case_id)),
            "CASEID": case_id,
        }

        deliverables_template = self.replace_in_dataframe(deliverables_template, replace_map)

        deliverables_template["path_index"] = "~"
        return deliverables_template

    def convert_deliverables_dataframe(self, dataframe: pd.DataFrame) -> dict:
        """Convert deliverables dataframe."""
        return dataframe.to_dict(orient="records").replace("'~'", "~")

    def report_deliver(self, case_id: str) -> None:
        """Get a deliverables file template from resources, parse it and, then write the deliverables file."""
        deliverables_template: pd.DataFrame = self.get_template_deliverables_file(
            resources.rnafusion_bundle_filenames_path
        )
        edited_deliverables: pd.DataFrame = self.edit_template_deliverables_file(
            case_id, deliverables_template
        )
        deliverables_file: dict = self.convert_deliverables_dataframe_to_dict(edited_deliverables)
        WriteFile.write_file_from_content(
            content=deliverables_file,
            file_format=FileFormat.YAML,
            file_path=self.get_deliverables_file_path(case_id),
        )
