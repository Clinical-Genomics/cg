"""NIPT ftp upload API"""
import datetime as dt
import logging
from pathlib import Path
import requests
from typing import Iterable, List, Optional

from requests import Response

import paramiko
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.exc import HousekeeperFileMissingError, StatinaAPIHTTPError
from cg.meta.upload.nipt.models import StatinaUploadFiles
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class NiptUploadAPI:
    """API for uploading the Fluffy analysis result file to the Klinisk Genetik ftp server"""

    RESULT_FILE_TAGS = ["nipt", "metrics"]

    def __init__(self, config: CGConfig):
        self.sftp_user: str = config.fluffy.sftp.user
        self.sftp_password: str = config.fluffy.sftp.password
        self.sftp_host: str = config.fluffy.sftp.host
        self.statina_host: str = config.statina.host
        self.sftp_port = config.fluffy.sftp.port
        self.sftp_remote_path = config.fluffy.sftp.remote_path
        self.root_dir = Path(config.housekeeper.root)
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run"""

        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def get_housekeeper_results_file(self, case_id: str, tags: Optional[list] = None) -> str:
        """Get the result file for a NIPT analysis from Housekeeper"""

        if not tags:
            tags: List[str] = self.RESULT_FILE_TAGS

        hk_all_results_file: hk_models.File = self.housekeeper_api.find_file_in_latest_version(
            case_id=case_id, tags=tags
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

    def get_all_upload_analyses(self) -> Iterable[models.Analysis]:
        """Gets all nipt analyses that are ready to be uploaded"""

        latest_nipt_analyses = self.status_db.latest_analyses().filter(
            models.Analysis.pipeline == Pipeline.FLUFFY
        )

        return latest_nipt_analyses.filter(models.Analysis.uploaded_at.is_(None))

    def upload_to_ftp_server(self, results_file: Path) -> None:
        """Upload the result file to the ftp server"""
        transport: paramiko.Transport = paramiko.Transport((self.sftp_host, self.sftp_port))
        LOG.info(f"Connecting to SFTP server {self.sftp_host}")
        transport.connect(username=self.sftp_user, password=self.sftp_password)
        sftp: paramiko.SFTPClient = paramiko.SFTPClient.from_transport(transport)
        LOG.info(
            f"Uploading file {str(results_file)} to remote path "
            f"{self.sftp_remote_path}/{results_file.name}"
        )
        sftp.put(
            localpath=str(results_file),
            remotepath=f"/{self.sftp_remote_path}/{results_file.name}",
            confirm=False,
        )
        sftp.close()
        transport.close()

    def update_analysis_uploaded_at_date(self, case_id: str) -> models.Analysis:
        """Updates analysis_uploaded_at for the uploaded analysis"""

        case_obj: models.Family = self.status_db.family(case_id)
        analysis_obj: models.Analysis = case_obj.analyses[0]

        if not self.dry_run:
            analysis_obj.uploaded_at = dt.datetime.now()
            self.status_db.commit()

        return analysis_obj

    def update_analysis_upload_started_date(self, case_id: str) -> models.Analysis:
        """Updates analysis_upload_started_at for the uploaded analysis"""

        case_obj: models.Family = self.status_db.family(case_id)
        analysis_obj: models.Analysis = case_obj.analyses[0]

        if not self.dry_run:
            analysis_obj.upload_started_at = dt.datetime.now()
            self.status_db.commit()

        return analysis_obj

    def get_statina_files(self, case_id: str) -> StatinaUploadFiles:
        """Get statina files from from housekeeper."""

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

        response: Response = requests.post(
            url=f"{self.statina_host}/insert/batch",
            headers={"Content-Type": "application/json"},
            data=statina_files.json(exclude_none=True),
        )
        if not response.ok:
            raise StatinaAPIHTTPError(response.text)

        LOG.info("nipt output: %s", response.text)
