"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import datetime as dt
import logging
import os
from pathlib import Path
from typing import List

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models

LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.hasta_path: str = config.external.hasta
        self.caesar_path: str = config.external.caesar
        self.base_path: str = config.data_delivery.base_path
        self.account: str = config.data_delivery.account
        self.mail_user: str = config.data_delivery.mail_user

    def create_log_dir(self, ticket_id: int, dry_run: bool) -> Path:
        timestamp = dt.datetime.now()
        timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name = Path("_".join([str(ticket_id), timestamp_str]))
        log_dir = Path(self.base_path) / folder_name
        LOG.info("Creating folder: %s", log_dir)
        if log_dir.exists():
            LOG.warning("Could not create %s, this folder already exist", log_dir)
        elif dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
        else:
            os.makedirs(log_dir)
        return log_dir

    def create_source_path(
        self, cust_id: str, ticket_id: int, raw_path: str, cust_sample_id: str
    ) -> str:
        cust_id_added_to_path = (
            raw_path % cust_id + "/" + str(ticket_id) + "/" + cust_sample_id + "/"
        )
        return cust_id_added_to_path

    def create_destination_path(self, cust_id: str, raw_path: str, lims_sample_id: str) -> str:
        cust_id_added_to_path = raw_path % cust_id + "/" + lims_sample_id + "/"
        return cust_id_added_to_path

    def download_sample(
        self, cust_id: str, ticket_id: int, cust_sample_id: str, lims_sample_id: str, dry_run: bool
    ) -> int:
        log_dir: Path = self.create_log_dir(ticket_id=ticket_id, dry_run=dry_run)
        source_path: str = self.create_source_path(
            cust_id=cust_id,
            ticket_id=ticket_id,
            raw_path=self.caesar_path,
            cust_sample_id=cust_sample_id,
        )
        destination_path: str = self.create_destination_path(
            cust_id=cust_id,
            raw_path=self.hasta_path,
            lims_sample_id=lims_sample_id,
        )
        commands = RSYNC_COMMAND.format(source_path=source_path, destination_path=destination_path)
        error_function = ERROR_RSYNC_FUNCTION.format()
        sbatch_info = {
            "job_name": "_".join([str(ticket_id), "rsync_external_data"]),
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": log_dir.as_posix(),
            "email": self.mail_user,
            "hours": 24,
            "commands": commands,
            "error": error_function,
        }
        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path = log_dir / "_".join([str(ticket_id), "rsync_external_data.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number

    def download_ticket(self, ticket_id: int, dry_run: bool) -> None:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        cust_id = cases[0].customer.internal_id
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id = link.sample.internal_id
                cust_sample_id = link.sample.name
                sbatch_number = self.download_sample(
                    cust_id=cust_id,
                    ticket_id=ticket_id,
                    cust_sample_id=cust_sample_id,
                    lims_sample_id=lims_sample_id,
                    dry_run=dry_run,
                )
                LOG.info(
                    "Downloading sample %s from caesar by submitting sbatch job %s",
                    (lims_sample_id, sbatch_number),
                )
