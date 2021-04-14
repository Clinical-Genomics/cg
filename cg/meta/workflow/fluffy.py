import csv
import datetime as dt
import logging
import os
import shutil
from abc import ABC
from pathlib import Path
from subprocess import CalledProcessError
from typing import List

from alchy import Query
from cg.constants import Pipeline
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class FluffyAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.FLUFFY,
    ):
        self.root_dir = Path(config.fluffy.root_dir)
        LOG.info("Set root dir to %s", config.fluffy.root_dir)
        self.fluffy_config = Path(config.fluffy.config_path)
        super().__init__(
            pipeline,
            config,
        )

    @property
    def threshold_reads(self):
        return False

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(binary=self.config.fluffy.binary_path)
        return self._process

    def get_samplesheet_path(self, case_id: str) -> Path:
        """
        Location in case folder where samplesheet is expected to be stored. Samplesheet is used as a config
        required to run Fluffy
        """
        return Path(self.root_dir, case_id, "SampleSheet.csv")

    def get_workdir_path(self, case_id: str) -> Path:
        """
        Location in case folder where all sub-folders for each sample containing fastq files are to e saved
        """
        return Path(self.root_dir, case_id, "fastq")

    def get_fastq_path(self, case_id: str, sample_id: str) -> Path:
        """
        Location in working directory to which fastq files are saved for each sample separately
        """
        return Path(self.get_workdir_path(case_id), sample_id)

    def get_output_path(self, case_id: str) -> Path:
        """
        Location in case directory where Fluffy outputs will be stored
        """
        return Path(self.root_dir, case_id, "output")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """
        Location in working directory where deliverables file will be stored upon completion of analysis.
        Deliverables file is used to communicate paths and tag definitions for files in a finished analysis
        """
        return Path(self.get_output_path(case_id), "deliverables.yaml")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """
        Location in working directory where SLURM job id file is to be stored.
        This file contains SLURM ID of jobs associated with current analysis ,
        is used as a config to be submitted to Trailblazer and track job progress in SLURM
        """
        return Path(self.get_output_path(case_id), "sacct", "submitted_jobs.yaml")

    def get_analysis_finish_path(self, case_id: str) -> Path:
        return Path(self.get_output_path(case_id), "analysis_finished")

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        """
        Links fastq files from Housekeeper to case working directory
        """
        case_obj: models.Family = self.status_db.family(case_id)
        workdir_path = self.get_workdir_path(case_id=case_id)
        if workdir_path.exists() and not dry_run:
            LOG.info("Fastq directory exists, removing and re-linking files!")
            shutil.rmtree(workdir_path, ignore_errors=True)
        workdir_path.mkdir(parents=True, exist_ok=True)
        for family_sample in case_obj.links:
            sample_id = family_sample.sample.internal_id
            files: Query = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])

            sample_path: Path = self.get_fastq_path(case_id=case_id, sample_id=sample_id)
            for file in files:
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    Path(sample_path / Path(file.full_path).name).symlink_to(file.full_path)
                LOG.info(f"Linking {file.full_path} to {sample_path / Path(file.full_path).name}")

    def get_concentrations_from_lims(self, sample_id: str) -> str:
        """Get sample concentration from LIMS"""
        return self.lims_api.get_sample_attribute(lims_id=sample_id, key="concentration_sample")

    def add_concentrations_to_samplesheet(
        self, samplesheet_housekeeper_path: Path, samplesheet_workdir_path: Path
    ) -> None:
        """
        Reads the fluffy samplesheet *.csv file as found in Housekeeper.
        Edits column 'SampleName' to include customer name for sample.
        Appends a column 'Library_nM' at the end of the csv with concentration values extracted from LIMS
        """
        csv_reader = csv.reader(open(samplesheet_housekeeper_path, "r"))
        csv_writer = csv.writer(open(samplesheet_workdir_path, "w"))

        sample_name_index = None
        sample_id_index = None
        for row in csv_reader:
            if "SampleID" in row and not sample_id_index:
                sample_name_index = row.index("SampleName")
                sample_id_index = row.index("SampleID")
                row.append("Library_nM")
                csv_writer.writerow(row)
                continue
            if sample_id_index:
                sample_id = row[sample_id_index]
                row[sample_name_index] = self.get_sample_name_from_lims_id(lims_id=sample_id)
                row.append(str(self.get_concentrations_from_lims(sample_id=sample_id)))
                csv_writer.writerow(row)

    def get_samplesheet_housekeeper_path(self, flowcell_name: str) -> Path:
        """
        Returns the path to original samplesheet file that is added to Housekeeper
        """
        samplesheet_query: list = self.housekeeper_api.files(
            bundle=flowcell_name, tags=["samplesheet"]
        ).all()
        if not samplesheet_query:
            LOG.error(
                "Samplesheet file for flowcell %s could not be found in Housekeeper!", flowcell_name
            )
            raise CgError
        return Path(samplesheet_query[0].full_path)

    def make_samplesheet(self, case_id: str, dry_run: bool) -> None:
        """
        Create SampleSheet.csv file in working directory and add desired values to the file
        """
        case_obj: models.Family = self.status_db.family(case_id)
        flowcell_name: str = case_obj.links[0].sample.flowcells[0].name
        samplesheet_housekeeper_path = self.get_samplesheet_housekeeper_path(
            flowcell_name=flowcell_name
        )
        samplesheet_workdir_path = Path(self.get_samplesheet_path(case_id=case_id))
        LOG.info(
            "Writing modified csv from %s to %s",
            samplesheet_housekeeper_path,
            samplesheet_workdir_path,
        )
        if not dry_run:
            Path(self.root_dir, case_id).mkdir(parents=True, exist_ok=True)
            self.add_concentrations_to_samplesheet(
                samplesheet_housekeeper_path=samplesheet_housekeeper_path,
                samplesheet_workdir_path=samplesheet_workdir_path,
            )

    def run_fluffy(self, case_id: str, dry_run: bool) -> None:
        """
        Call fluffy with the configured command-line arguments
        """
        output_path: Path = self.get_output_path(case_id=case_id)
        if output_path.exists():
            LOG.info("Old working directory found, cleaning!")
            if not dry_run:
                shutil.rmtree(output_path, ignore_errors=True)
        command_args = [
            "--config",
            self.fluffy_config.as_posix(),
            "--sample",
            self.get_samplesheet_path(case_id=case_id).as_posix(),
            "--project",
            self.get_workdir_path(case_id=case_id).as_posix(),
            "--out",
            self.get_output_path(case_id=case_id).as_posix(),
            "analyse",
        ]
        self.process.run_command(command_args, dry_run=dry_run)

    def get_cases_to_store(self) -> List[models.Family]:
        """Retrieve a list of cases where analysis finished successfully,
        and is ready to be stored in Housekeeper"""
        return [
            case_object
            for case_object in self.get_running_cases()
            if Path(self.get_analysis_finish_path(case_id=case_object.internal_id)).exists()
        ]
