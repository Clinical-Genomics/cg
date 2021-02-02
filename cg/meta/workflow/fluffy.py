from pathlib import Path
import logging
import csv
from subprocess import CalledProcessError
from typing import Any, Optional

from ruamel.yaml import safe_load
import datetime as dt

from cg.apps.hermes.hermes_api import HermesApi
from cg.exc import BundleAlreadyAddedError
from cg.utils import Process
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.lims import LimsAPI
from cg.store import Store, models
import os
from cg.constants import Pipeline, CASE_ACTIONS

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

    def get_workdir_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "fastq")

    def get_samplesheet_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "SampleSheet.csv")

    def get_fastq_path(self, case_id: str, sample_id: str) -> Path:
        return Path(self.root_dir, case_id, "fastq", sample_id)

    def get_output_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output")

    def get_deliverables_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output", "deliverables.yaml")

    def get_slurm_job_ids_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output", "sacct", "submitted_jobs.yaml")

    def get_priority(self, case_id: str) -> str:
        """Returns priority for the case in clinical-db as text"""
        case_object = self.status_db.family(case_id)
        if case_object:
            if case_object.high_priority:
                return "high"
            if case_object.low_priority:
                return "low"
        return "normal"

    def get_sample_name_from_lims_id(self, lims_id: str) -> str:
        LOG.info("getting sample name of %s", lims_id)
        sample_obj = self.status_db.sample(lims_id)
        return sample_obj.name

    def link_fastq_files(self, case_id: str, dry_run: bool) -> None:
        """
        1. Get fastq from HK
        2. Copy sample fastq to root_dir/case_id/fastq/sample_id (from samplesheet)
        """
        case_obj = self.status_db.family(case_id)
        workdir_path = self.get_workdir_path(case_id=case_id)
        if workdir_path.exists():
            workdir_path.rmdir()
        for familysample in case_obj.links:
            sample_id = familysample.sample.internal_id
            files = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
            sample_path: Path = self.get_fastq_path(case_id=case_id, sample_id=sample_id)
            for file in files:
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    Path(sample_path / Path(file.full_path).name).symlink_to(file.full_path)
                LOG.info(f"Linking {file.full_path} to {sample_path / Path(file.full_path).name}")

    def get_concentrations_from_lims(self, sample_id: str) -> str:
        # placeholder
        # When samplesheet is uploaded to lims on stage, replace with LIMS query
        return self.lims_api.get_sample_attribute(lims_id=sample_id, key="Sample Conc.")

    def add_concentrations_to_samplesheet(
        self, samplesheet_housekeeper_path: Path, samplesheet_workdir_path: Path
    ) -> None:
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

    def make_samplesheet(self, case_id: str, dry_run: bool) -> None:

        """
        1. Get samplesheet from HK
        2. Copy file to root_dir/case_id/samplesheet.csv
        """
        case_obj = self.status_db.family(case_id)
        flowcell_name = case_obj.links[0].sample.flowcells[0].name
        samplesheet_housekeeper_path = Path(
            self.housekeeper_api.files(bundle=flowcell_name, tags=["samplesheet"])
            .all()[0]
            .full_path
        )
        samplesheet_workdir_path = Path(self.get_samplesheet_path(case_id=case_id))
        LOG.info(
            "Writing modified csv from %s to %s",
            samplesheet_housekeeper_path,
            samplesheet_workdir_path,
        )
        if not dry_run:
            self.add_concentrations_to_samplesheet(
                samplesheet_housekeeper_path=samplesheet_housekeeper_path,
                samplesheet_workdir_path=samplesheet_workdir_path,
            )

    def run_fluffy(self, case_id: str, dry_run: bool) -> None:

        output_path: Path = self.get_output_path(case_id=case_id)
        if output_path.exists():
            LOG.info("Old working directory found, cleaning!")
            output_path.rmdir()
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
        deliverables_path = self.get_deliverables_path(case_id=case_id)
        analysis_date = self.get_date_from_file_path(file_path=deliverables_path)
        bundle_data = self.hermes_api.create_housekeeper_bundle(
            deliverables=deliverables_path,
            pipeline="fluffy",
            created=analysis_date,
            analysis_type=None,
            bundle_name=case_id,
        ).dict()
        bundle_data["name"] = case_id

        bundle_result = self.housekeeper_api.add_bundle(bundle_data=bundle_data)
        if not bundle_result:
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_bundle_statusdb(self, case_id: str) -> None:
        case_obj: models.Family = self.status_db.family(case_id)
        analysis_date = self.get_date_from_file_path(
            deliverables_path=self.get_deliverables_path(case_id=case_id)
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
        """ Get date from deliverables path using date created metadata """
        return dt.datetime.fromtimestamp(int(os.path.getctime(file_path)))

    def get_cases_to_store(self) -> list:
        return [
            case_obj
            for case_obj in self.status_db.cases_to_store(pipeline=Pipeline.FLUFFY)
            if self.get_deliverables_path(case_id=case_obj.internal_id).exists()
        ]

    def get_pipeline_version(self) -> str:
        try:
            self.process.run_command(["--version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except CalledProcessError:
            LOG.warning("Could not retrieve fluffy version!")
            return "0.0.0"

    def set_statusdb_action(self, case_id: str, action: Optional[str]) -> None:
        if action in [None, *CASE_ACTIONS]:
            case_object: models.Family = self.status_db.family(case_id)
            case_object.action = action
            self.status_db.commit()
            LOG.info("Action %s set for case %s", action, case_id)
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {case_id}"
        )
