"""NIPT ftp upload API"""
import logging
from pathlib import Path
from typing import Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.utils import Process
from housekeeper.store import Store

LOG = logging.getLogger(__name__)


class NiptUploadAPI:
    """API for NIPT upload via ftp"""

    RESULT_FILE_TAGS = ["nipt", "metrics"]

    def __init__(self, config: CGConfig):
        self.sftp_user: str = config.fluffy.sftp.user
        self.sftp_password: str = config.fluffy.sftp.password
        self.sftp_host: str = config.fluffy.sftp.host
        self.root_dir = Path(config.housekeeper.root)
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.process = Process(binary="lftp")
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run"""

        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def get_housekeeper_results_file(self, case_id: str, tags: Optional[list] = None) -> str:
        """Get the result file for a NIPT analysis from Housekeeper"""

        if not tags:
            tags = self.RESULT_FILE_TAGS

        hk_results_file = self.housekeeper_api.get_files(bundle=case_id, tags=tags).first().path

        if not hk_results_file:
            raise FileNotFoundError(
                f"No results file found in Housekeeper for NIPT case {case_id}."
            )
        return hk_results_file

    def get_results_file_path(self, hk_results_file) -> Path:
        """Get the full path to the results file on Hasta"""

        results_file = self.root_dir / Path(hk_results_file)

        if not results_file.exists():
            raise FileNotFoundError(f"Results file {results_file} not found on hasta!")

        return results_file

    def get_all_upload_analyses(self):
        """Gets all nipt analyses that are ready to be uploaded"""

        latest_nipt__analyses = self.status_db.latest_analyses().filter(
            models.Analysis.pipeline == Pipeline.FLUFFY
        )

        return latest_nipt__analyses.filter(models.Analysis.uploaded_at.is_(None))

    def upload(self, results_file: Path) -> None:
        """Upload the result file to the ftp server"""

        parameters: list = [
            f"sftp://{self.sftp_user}:{self.sftp_password}" f"@{self.sftp_host}",
            "-e",
            f'"cd SciLife_Till_StarLims; put {results_file}; bye"',
        ]

        self.process.run_command(parameters=parameters, dry_run=self.dry_run)

        if self.process.stderr:
            LOG.info(f"NIPT Upload stderr:\n{self.process.stderr}")
        if self.process.stdout:
            LOG.info(f"NIPT Upload stdout:\n{self.process.stdout}")
