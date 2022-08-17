"""Module for Balsamic Analysis API"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Union, Any
import pandas as pd
import os

import yaml
from pydantic import ValidationError
from cg.constants import DataDelivery, Pipeline
from cg.exc import RnafusionStartError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import RnafusionFastqHandler
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.utils import Process
from cg import resources
from datetime import datetime

LOG = logging.getLogger(__name__)


class RnafusionAnalysisAPI(AnalysisAPI):
    """Handles communication between RNAFUSION processes
    and the rest of CG infrastructure"""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RNAFUSION,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir = config.rnafusion.root
        self.nfcore_pipeline_path = config.rnafusion.pipeline_path
        self.references = config.rnafusion.references
        self.profile = config.rnafusion.profile
        self.conda_env = config.rnafusion.conda_env

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return RnafusionFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(self.config.rnafusion.binary_path, None, None, self.conda_env)
        return self._process

    def get_case_path(self, case_id: str) -> Path:
        """Returns a path where the rnafusion case should be located"""
        return Path(self.root_dir, case_id)

    def get_case_config_path(self, case_id: str) -> Path:
        """Generates a path where the Rnafusion samplesheet for the case_id should be located."""
        return Path((self.get_case_path(case_id)), case_id + "_samplesheet.csv")

    def make_case_folder(self, case_id: str) -> None:
        """Make the case folder where rnafusion analysis should be located"""
        self.get_case_path(case_id)
        os.makedirs(self.get_case_path(case_id), exist_ok=True)

    def write_samplesheet(self, case_id: str, strandedness="reverse") -> None:
        """Write samplesheet for rnafusion analysis in case folder"""
        case_obj = self.status_db.family(case_id)
        for link in case_obj.links:
            file_collection = pd.DataFrame(self.gather_file_metadata_for_sample(link.sample))
            file_collection = file_collection.sort_values(by=["path"])
            fastq_r1 = file_collection[file_collection["read"] == 1]["path"].to_list()
            fastq_r2 = file_collection[file_collection["read"] == 2]["path"].to_list()
            samplesheet = pd.DataFrame(
                list(zip(fastq_r1, fastq_r2)), columns=["fastq_1", "fastq_2"]
            )
            samplesheet["sample"] = case_id
            samplesheet["strandedness"] = strandedness
            filename = self.get_case_config_path(case_id)
            LOG.info("Writing samplesheet for case " + case_id + " to " + str(filename))
            samplesheet.to_csv(
                filename, index=False, columns=["sample", "fastq_1", "fastq_2", "strandedness"]
            )

    def get_log_path(self, case_id: str, log: str = None) -> Path:
        if log:
            return log
        dt = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(self.get_case_path(case_id), case_id + "rnafusion_nextflow_log_" + dt + ".log")

    def get_profile(self, profile: str = None) -> Path:
        if profile:
            return profile
        return self.profile

    def get_workdir_path(self, case_id: str, work_dir: str = None) -> Path:
        if work_dir:
            return work_dir
        return Path(self.get_case_path(case_id), "work")

    def get_input_path(self, case_id: str, input: str = None) -> Path:
        if input:
            return input
        return Path(self.get_case_config_path(case_id))

    def get_outdir_path(self, case_id: str, outdir: str = None) -> Path:
        if outdir:
            return outdir
        return Path(self.get_case_path(case_id))

    def get_references_path(self, genomes_bases: str = None) -> Path:
        if genomes_bases:
            return genomes_bases
        return Path(self.references)

    def get_verified_arguments(
        self,
        case_id: str,
        work_dir: str,
        resume: bool,
        profile: str,
        with_tower: bool,
        stub: bool,
        input: str,
        outdir: str,
        genomes_base: str,
        trim: bool,
        fusioninspector_filter: bool,
        all: bool,
        pizzly: bool,
        squid: bool,
        starfusion: bool,
        fusioncatcher: bool,
        arriba: bool,
    ) -> dict:
        """This is a function to document"""

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
        log: str,
    ) -> dict:
        """This is a function to document"""

        return {
            "-log": self.get_log_path(case_id, log),
        }

    def get_pipeline_version(self, case_id: str) -> str:
        try:
            self.process.run_command(["-version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except (Exception, CalledProcessError):
            LOG.warning("Could not retrieve %s workflow version!", self.pipeline)
            return "0.0.0"

    @staticmethod
    def __build_command_str(options: dict) -> List[str]:
        formatted_options = []
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
        """Create samplesheet file for RNAFUSION analysis"""
        self.make_case_folder(case_id)
        if not (self.get_case_config_path(case_id)).is_file():
            LOG.info("Samplesheet does not exist, writing samplesheet")
            self.write_samplesheet(case_id, strandedness)
        LOG.info("Samplesheet written")

    def run_analysis(
        self,
        case_id: str,
        log: str,
        work_dir: str,
        resume: bool,
        profile: str,
        with_tower: bool,
        stub: bool,
        input: str,
        outdir: str,
        genomes_base: str,
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
        """Execute RNAFUSION run analysis with given options"""

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
            + [
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
        )
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_cases_to_analyze(self) -> List[models.Family]:
        cases_query: List[models.Family] = self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )
        cases_to_analyze = []
        for case_obj in cases_query:
            if case_obj.action == "analyze" or not case_obj.latest_analyzed:
                cases_to_analyze.append(case_obj)
        return cases_to_analyze

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the rnafusion deliverables file for the case_id should be located.

        (Optional) Checks if deliverables file exists
        """
        return Path(self.get_case_path(case_id), case_id + "_deliverables.yaml")

    def report_deliver(self, case_id: str) -> None:
        """Write report deliver"""
        df = pd.read_csv(resources.rnafusion_bundle_filenames_path)
        df = df.replace({"PATHTOCASE": str(self.get_case_path(case_id))}, regex=True)
        df = df.replace({"CASEID": case_id}, regex=True)
        df["path_index"] = "~"
        text = yaml.dump(df.to_dict(orient="records")).replace("'~'", "~")
        deliver_file = open(self.get_deliverables_file_path(case_id), "w")
        deliver_file.write("files:\n")
        deliver_file.write(text)
        deliver_file.close()
