from pathlib import Path
import logging
from ruamel.yaml import safe_load
import datetime as dt
from cg.utils import Process
from cg.apps.NIPTool import NIPToolAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class FluffyAnalysisAPI:
    def __init__(
        self,
        housekeeper_api: HousekeeperAPI,
        trailblazer_api: TrailblazerAPI,
        niptool_api: NIPToolAPI,
        status_db: Store,
        root_dir: str,
        binary: str,
    ):
        self.housekeeper_api = housekeeper_api
        self.trailblazer_api = trailblazer_api
        self.niptool_api = niptool_api
        self.status_db = status_db
        self.root_dir = Path(root_dir)
        self.process = Process(binary=binary)

    def get_samplesheet_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "samplesheet.csv")

    def get_fastq_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "fastq")

    def get_output_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output")

    def get_deliverables_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output", "deliverables.yaml")

    def get_slurm_job_ids_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "output", "sacct", "submitted_jobs.yaml")

    def get_priority(self, case_id: str) -> str:
        case_object = self.status_db.family(case_id)
        if case_object.high_priority:
            return "high"
        if case_object.low_priority:
            return "low"
        return "normal"

    def link_fastq(self, case_id: str, dry_run: bool) -> None:
        """
        1. Get fastq from HK
            1a. If split by 4 lanes, concatenate
        2. Copy sample fastq to root_dir/case_id/fastq/sample_id (from samplesheet)
        """
        case_obj = self.status_db.family(case_id)
        for familysample in case_obj.links:
            sample_id = familysample.sample.internal_id
            nipt_id = familysample.sample.name
            files = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
            for file in files:
                # Link files
                sample_path = self.get_fastq_path(case_id=case_id) / nipt_id
                if not dry_run:
                    Path.mkdir(sample_path, exist_ok=True, parents=True)
                    # Link and concatenate if necessary
                LOG.info(f"Linking {file.path} to {sample_path / Path(file.path).name}")

    def link_samplesheet(self, case_id: str, dry_run: bool) -> None:

        """
        1. Get samplesheet from HK
        2. Copy file to root_dir/case_id/samplesheet.csv
        """
        case_obj = self.status_db.family(case_id)
        case_name = case_obj.name
        samplesheet_housekeeper_path = Path(
            self.housekeeper_api.files(bundle=case_name, tags=["samplesheet"])[0].path
        )
        if not dry_run:
            LOG.info(f"Placeholder to actually link")

        LOG.info(
            f"Linking {samplesheet_housekeeper_path} to {self.get_samplesheet_path(case_id=case_id)}"
        )

    def run_fluffy(self, case_id: str, dry_run: bool) -> None:
        command_args = [
            "--sample",
            self.get_samplesheet_path(case_id=case_id).as_posix(),
            "--project",
            self.get_fastq_path(case_id=case_id).as_posix(),
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
