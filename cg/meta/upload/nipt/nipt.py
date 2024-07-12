"""NIPT ftp upload API"""

import datetime as dt
import logging
from pathlib import Path

import paramiko
import requests
from housekeeper.store.models import File
from requests import Response

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Workflow
from cg.exc import HousekeeperFileMissingError, StatinaAPIHTTPError
from cg.meta.upload.nipt.models import SequencingRunQ30AndReads, StatinaUploadFiles
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case, IlluminaSequencingRun
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class NiptUploadAPI:
    """API for uploading the Fluffy analysis result file to the Klinisk Genetik ftp server"""

    RESULT_FILE_TAGS = ["nipt", "metrics"]

    def __init__(self, config: CGConfig):
        self.sftp_user: str = config.fluffy.sftp.user
        self.sftp_password: str = config.fluffy.sftp.password
        self.sftp_host: str = config.fluffy.sftp.host
        self.statina_user: str = config.statina.user
        self.statina_password: str = config.statina.key
        self.statina_auth_url: str = config.statina.api_url + config.statina.auth_path
        self.statina_upload_url: str = config.statina.api_url + config.statina.upload_path
        self.sftp_port = config.fluffy.sftp.port
        self.sftp_remote_path = config.fluffy.sftp.remote_path
        self.root_dir = Path(config.housekeeper.root)
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.dry_run: bool = False
        self.trailblazer_api: TrailblazerAPI = config.trailblazer_api

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run"""

        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def sequencing_run_passed_qc_value(self, case_id: str, q30_threshold: float) -> bool:
        """
        Check the average Q30 and the total number of reads for each sample
        in the latest sequencing run related to a case.
        """
        sequencing_run: IlluminaSequencingRun = (
            self.status_db.get_latest_illumina_sequencing_run_for_nipt_case(case_id)
        )
        sequencing_run_summary: SequencingRunQ30AndReads = SequencingRunQ30AndReads(
            average_q30_across_samples=sequencing_run.percent_q30,
            total_reads_on_flow_cell=sequencing_run.total_reads,
        )
        threshold: int = self.status_db.get_ready_made_library_expected_reads(case_id=case_id)
        if not sequencing_run_summary.passes_q30_threshold(
            threshold=q30_threshold
        ) or not sequencing_run_summary.passes_read_threshold(threshold=threshold):
            LOG.warning(
                f"Sequencing run {sequencing_run.device.internal_id} did not pass QC for case {case_id} with Q30: "
                f"{sequencing_run_summary.average_q30_across_samples} and reads: {sequencing_run_summary.total_reads_on_flow_cell}."
                f"Skipping upload."
            )
            return False
        LOG.debug(
            f"Sequencing run for {sequencing_run.device.internal_id} passed QC for case {case_id}."
        )
        return True

    def get_housekeeper_results_file(self, case_id: str, tags: list | None = None) -> str:
        """Get the result file for a NIPT analysis from Housekeeper"""

        if not tags:
            tags: list[str] = self.RESULT_FILE_TAGS

        hk_all_results_file: File = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=tags
        )

        if not hk_all_results_file:
            raise HousekeeperFileMissingError(
                f"No results files found in Housekeeper for NIPT case {case_id}."
            )

        return hk_all_results_file.path

    def get_results_file_path(self, hk_results_file: str) -> Path:
        """Get the full path to the results file on Hasta"""

        results_file: Path = self.root_dir / hk_results_file

        if not results_file.exists():
            raise FileNotFoundError(f"Results file {results_file} not found on hasta!")

        return results_file

    def get_all_upload_analyses(self) -> list[Analysis]:
        """Gets all nipt analyses that are ready to be uploaded"""
        return self.status_db.get_latest_analysis_to_upload_for_workflow(workflow=Workflow.FLUFFY)

    def upload_to_ftp_server(self, results_file: Path) -> None:
        """Upload the result file to the ftp server"""
        if self.dry_run:
            LOG.info(f"Would upload results file to ftp server: {results_file}")
            return
        transport: paramiko.Transport = paramiko.Transport((self.sftp_host, self.sftp_port))
        LOG.info(f"Connecting to SFTP server {self.sftp_host}")
        transport.connect(username=self.sftp_user, password=self.sftp_password)
        sftp: paramiko.SFTPClient = paramiko.SFTPClient.from_transport(transport)
        LOG.info(
            f"Uploading file {results_file} to remote path {self.sftp_remote_path}/{results_file.name}"
        )

        sftp.put(
            localpath=str(results_file),
            remotepath=f"/{self.sftp_remote_path}/{results_file.name}",
            confirm=False,
        )
        sftp.close()
        transport.close()

    def update_analysis_uploaded_at_date(self, case_id: str) -> Analysis:
        """Updates analysis_uploaded_at for the uploaded analysis"""

        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis_obj: Analysis = case_obj.analyses[0]

        if not self.dry_run:
            analysis_obj.uploaded_at = dt.datetime.now()
            self.status_db.session.commit()
            self.trailblazer_api.set_analysis_uploaded(
                case_id=case_id, uploaded_at=analysis_obj.uploaded_at
            )

        return analysis_obj

    def update_analysis_upload_started_date(self, case_id: str) -> Analysis:
        """Updates analysis_upload_started_at for the uploaded analysis"""

        case_obj: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis_obj: Analysis = case_obj.analyses[0]

        if not self.dry_run:
            analysis_obj.upload_started_at = dt.datetime.now()
            self.status_db.session.commit()

        return analysis_obj

    def get_statina_files(self, case_id: str) -> StatinaUploadFiles:
        """Get statina files from housekeeper."""

        hk_results_file: str = self.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "metrics"]
        )
        results_file: Path = self.get_results_file_path(hk_results_file)

        hk_multiqc_file: str = self.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "multiqc-html"]
        )
        multiqc_file: Path = self.get_results_file_path(hk_multiqc_file)

        hk_segmental_calls_file: str = self.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "wisecondor"]
        )
        segmental_calls_file: Path = self.get_results_file_path(hk_segmental_calls_file)

        return StatinaUploadFiles(
            result_file=results_file.absolute().as_posix(),
            multiqc_report=multiqc_file.absolute().as_posix(),
            segmental_calls=segmental_calls_file.parent.as_posix(),
        )

    def upload_to_statina_database(self, statina_files: StatinaUploadFiles):
        """Upload nipt data via rest-API."""

        token: str = (
            requests.post(
                self.statina_auth_url,
                data={"username": self.statina_user, "password": self.statina_password},
            )
            .json()
            .get("access_token")
        )

        response: Response = requests.post(
            url=self.statina_upload_url,
            headers={"authorization": f"Bearer {token}"},
            data=statina_files.json(exclude_none=True),
        )
        if not response.ok:
            LOG.error(response.text)
            raise StatinaAPIHTTPError(response.text)

        LOG.info("nipt output: %s", response.text)
