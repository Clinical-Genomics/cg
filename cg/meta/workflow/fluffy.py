from pathlib import Path
import logging
import csv
from ruamel.yaml import safe_load
import datetime as dt
from cg.utils import Process
from cg.apps.NIPTool import NIPToolAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.lims import LimsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class FluffyAnalysisAPI:
    def __init__(
        self,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: TrailblazerAPI,
        lims_api: LimsAPI,
        niptool_api: NIPToolAPI,
        status_db: Store,
        config: dict,
    ):
        self.housekeeper_api = housekeeper_api
        self.trailblazer_api = trailblazer_api
        self.niptool_api = niptool_api
        self.status_db = status_db
        self.lims_api = lims_api
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

    def link_fastq_files(self, case_id: str, dry_run: bool) -> None:
        """
        1. Get fastq from HK
        2. Copy sample fastq to root_dir/case_id/fastq/sample_id (from samplesheet)
        """
        case_obj = self.status_db.family(case_id)
        for familysample in case_obj.links:
            sample_id = familysample.sample.internal_id
            files = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
            sample_path = self.get_fastq_path(case_id=case_id, sample_id=sample_id)
            for file in files:
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    Path(file.path).symlink_to(sample_path, target_is_directory=True)
                LOG.info(f"Linking {file.path} to {sample_path / Path(file.path).name}")

    def get_concentrations_from_lims(self, sample_id: str) -> float:
        # placeholder
        # When samplesheet is uploaded to lims on stage, replace with LIMS query
        return 50.0

    def add_concentrations_to_samplesheet(
        self, samplesheet_housekeeper_path: Path, samplesheet_workdir_path: Path
    ) -> None:
        csv_reader = csv.reader(open(samplesheet_housekeeper_path, "r"), delimiter=",")
        csv_writer = csv.writer(open(samplesheet_workdir_path, "w"), delimiter=",")

        sampleid_index = None
        csv_columns = None
        for row in csv_reader:
            if not sampleid_index and "SampleID" in row:
                sampleid_index = row.index("SampleID")
                csv_columns = len(row)
                csv_writer.writerow(row.append("Library_nM"))
            if csv_columns and len(row) == csv_columns:
                sample_id = row[sampleid_index]
                csv_writer.writerow(
                    row.append(self.get_concentrations_from_lims(sample_id=sample_id))
                )

    def make_samplesheet(self, case_id: str, dry_run: bool) -> None:

        """
        1. Get samplesheet from HK
        2. Copy file to root_dir/case_id/samplesheet.csv
        """
        case_obj = self.status_db.family(case_id)
        flowcell_name = case_obj.links[0].sample.flowcells[0].name
        samplesheet_housekeeper_path = Path(
            self.housekeeper_api.files(bundle=flowcell_name, tags=["samplesheet"])[0].path
        )
        samplesheet_workdir_path = Path(self.get_samplesheet_path(case_id=case_id))
        LOG.info("Writing modified csv from to %s", samplesheet_workdir_path)
        if not dry_run:
            self.add_concentrations_to_samplesheet(
                samplesheet_housekeeper_path=samplesheet_housekeeper_path,
                samplesheet_workdir_path=samplesheet_workdir_path,
            )

    def run_fluffy(self, case_id: str, dry_run: bool) -> None:
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

    def parse_deliverables(self, case_id) -> list:
        deliverables_yaml = self.get_deliverables_path(case_id=case_id)
        deliverables_dict = safe_load(open(deliverables_yaml))
        deliverable_files = deliverables_dict["files"]
        bundle_files = []
        for entry in deliverable_files:
            bundle_file = {"path": entry["path"], "archive": False, "tags": [entry["tag"]]}
            bundle_files.append(bundle_file)
        return bundle_files

    def upload_bundle_housekeeper(self, case_id: str):
        bundle_data = {
            "name": case_id,
            "created": dt.datetime.now(),
            "files": self.parse_deliverables(case_id=case_id),
        }
        bundle_result = self.housekeeper_api.add_bundle(bundle_data=bundle_data)
        bundle_object, bundle_version = bundle_result
        self.housekeeper_api.include(bundle_version)
        self.housekeeper_api.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def upload_results(self, case_id):
        """Upload to NIPT viewer
        Needs:

            StatusDB get project id

            Hk api get samplesheet
            Hk api get multiqc
            Hk api get results csv


        """
        pass
