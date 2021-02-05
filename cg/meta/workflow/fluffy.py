from pathlib import Path
import logging
import csv
from subprocess import CalledProcessError
from typing import Any, Optional, Tuple

import shutil
import datetime as dt

from alchy import Query

from cg.apps.hermes.hermes_api import HermesApi
from cg.exc import BundleAlreadyAddedError, CgError
from cg.utils import Process
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.lims import LimsAPI
from cg.store import Store, models
import os
from cg.constants import Pipeline, CASE_ACTIONS
from housekeeper.store.models import Bundle, Version

LOG = logging.getLogger(__name__)


class FluffyAnalysisAPI:
    def __init__(
        self,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: TrailblazerAPI,
        hermes_api: HermesApi,
        lims_api: LimsAPI,
        status_db: Store,
        config: dict,
    ):
        self.housekeeper_api = housekeeper_api
        self.trailblazer_api = trailblazer_api
        self.status_db = status_db
        self.lims_api = lims_api
        self.hermes_api = hermes_api
        self.root_dir = Path(config["root_dir"])
        self.process = Process(binary=config["binary_path"])
        self.fluffy_config = Path(config["config_path"])

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

    def get_deliverables_path(self, case_id: str) -> Path:
        """
        Location in working directory where deliverables file will be stored upon completion of analysis.
        Deliverables file is used to communicate paths and tag definitions for files in a finished analysis
        """
        return Path(self.get_output_path(case_id), "deliverables.yaml")

    def get_slurm_job_ids_path(self, case_id: str) -> Path:
        """
        Location in working directory where SLURM job id file is to be stored.
        This file contains SLURM ID of jobs associated with current analysis ,
        is used as a config to be submitted to Trailblazer and track job progress in SLURM
        """
        return Path(self.get_output_path(case_id), "sacct", "submitted_jobs.yaml")

    def get_priority(self, case_id: str) -> str:
        """Returns priority for the case in clinical-db as text"""
        case_obj: models.Family = self.status_db.family(case_id)
        if case_obj:
            if case_obj.high_priority:
                return "high"
            if case_obj.low_priority:
                return "low"
        return "normal"

    def verify_case_id_in_database(self, case_id: str) -> None:
        """
        Passes silently if case exists in StatusDB, raises error if case is missing
        """
        case_obj = self.status_db.family(case_id)
        if not case_obj:
            LOG.error("Case %s could not be found in StatusDB!", case_id)
            raise CgError

    def get_sample_name_from_lims_id(self, lims_id: str) -> str:
        """
        Retrieve sample name provided by customer for specific sample
        """
        LOG.debug("Setting sample name for %s", lims_id)
        sample_obj = self.status_db.sample(lims_id)
        return sample_obj.name

    def link_fastq_files(self, case_id: str, dry_run: bool) -> None:
        """
        Links fastq files from Housekeeper to case working directory
        """
        case_obj: models.Family = self.status_db.family(case_id)
        workdir_path = self.get_workdir_path(case_id=case_id)
        if workdir_path.exists() and not dry_run:
            LOG.info("Fastq directory exists, removing and re-linking files!")
            shutil.rmtree(workdir_path, ignore_errors=True)
        workdir_path.mkdir(parents=True, exist_ok=True)
        for familysample in case_obj.links:
            sample_id = familysample.sample.internal_id
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

    def upload_bundle_housekeeper(self, case_id: str) -> None:
        """
        Save the completed analysis bundle in Housekeeper
        """
        deliverables_path = self.get_deliverables_path(case_id=case_id)
        if not deliverables_path.exists():
            LOG.error("Deliverables file not found for case %s, aborting!", case_id)
            raise CgError
        analysis_date = self.get_date_from_file_path(file_path=deliverables_path)
        bundle_data = self.hermes_api.create_housekeeper_bundle(
            deliverables=deliverables_path,
            pipeline="fluffy",
            created=analysis_date,
            analysis_type=None,
            bundle_name=case_id,
        ).dict()
        bundle_data["name"] = case_id
        bundle_result: Tuple[Bundle, Version] = self.housekeeper_api.add_bundle(
            bundle_data=bundle_data
        )
        if not bundle_result:
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_bundle_statusdb(self, case_id: str) -> None:
        """
        Create completed analysis object in StatusDB
        """
        case_obj: models.Family = self.status_db.family(case_id)
        analysis_date = self.get_date_from_file_path(
            file_path=self.get_deliverables_path(case_id=case_id)
        )
        new_analysis: models.Analysis = self.status_db.add_analysis(
            pipeline=Pipeline.FLUFFY,
            started_at=self.get_date_from_file_path(
                file_path=self.get_samplesheet_path(case_id=case_id)
            ),
            version=self.get_pipeline_version(),
            completed_at=self.get_date_from_file_path(
                file_path=self.get_deliverables_path(case_id=case_id)
            ),
            primary=(len(case_obj.analyses) == 0),
        )
        new_analysis.family = case_obj
        self.status_db.add_commit(new_analysis)
        LOG.info(f"Analysis successfully stored in StatusDB: {case_id} : {analysis_date}")

    @staticmethod
    def get_date_from_file_path(file_path: Path) -> dt.datetime.date:
        """
        Get date from deliverables path using date created metadata.
        """
        return dt.datetime.fromtimestamp(int(os.path.getctime(file_path)))

    def get_cases_to_store(self) -> list:
        """
        Get a list of cases with action 'running' and existing deliverables file.
        """
        return [
            case_obj
            for case_obj in self.status_db.cases_to_store(pipeline=Pipeline.FLUFFY)
            if self.get_deliverables_path(case_id=case_obj.internal_id).exists()
        ]

    def get_pipeline_version(self) -> str:
        """
        Calls the pipeline to get the pipeline version number. If fails, returns a placeholder value instead.
        """
        try:
            self.process.run_command(["--version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except (Exception, CalledProcessError):
            LOG.warning("Could not retrieve fluffy version!")
            return "0.0.0"

    def set_statusdb_action(self, case_id: str, action: Optional[str]) -> None:
        """
        Set one of the allowed actions on a case in StatusDB.
        """
        if action in [None, *CASE_ACTIONS]:
            case_obj: models.Family = self.status_db.family(case_id)
            case_obj.action = action
            self.status_db.commit()
            LOG.info("Action %s set for case %s", action, case_id)
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {case_id}"
        )
