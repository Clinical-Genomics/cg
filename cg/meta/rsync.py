"""Module for building the rsync command to send files to customer inbox on caesar"""
import datetime
import glob
import logging
import os
from pathlib import Path
from typing import List

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.meta.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION, COVID_RSYNC
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cgmodels.cg.constants import Pipeline

LOG = logging.getLogger(__name__)


class RsyncAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.delivery_path: str = config.delivery_path
        self.destination_path: str = config.data_delivery.destination_path
        self.covid_destination_path: str = config.data_delivery.covid_destination_path
        self.covid_report_path: str = config.data_delivery.covid_report_path
        self.base_path: str = config.data_delivery.base_path
        self.account: str = config.data_delivery.account
        self.mail_user: str = config.data_delivery.mail_user

    def get_all_cases_from_ticket(self, ticket_id: int) -> List[models.Family]:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        return cases

    def get_source_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()
        customer_id: str = cases[0].customer.internal_id
        delivery_source_path: str = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return delivery_source_path

    def get_destination_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        customer_id: str = cases[0].customer.internal_id
        rsync_destination_path: str = (
            Path(self.destination_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return rsync_destination_path

    def create_log_dir(self, ticket_id: int, dry_run: bool) -> Path:
        timestamp = datetime.datetime.now()
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

    def run_rsync_on_slurm(self, ticket_id: int, dry_run: bool) -> int:
        log_dir: Path = self.create_log_dir(ticket_id=ticket_id, dry_run=dry_run)
        source_path: str = self.get_source_path(ticket_id=ticket_id)
        destination_path: str = self.get_destination_path(ticket_id=ticket_id)
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        customer_id: str = cases[0].customer.internal_id
        if cases[0].data_analysis == Pipeline.SARS_COV_2:
            LOG.info("Delivering report for SARS-COV-2 analysis")
            covid_report_options: List[str] = glob.glob(
                self.covid_report_path % (str(cases[0].internal_id), ticket_id)
            )
            if not covid_report_options:
                LOG.error(
                    f"No report file could be found with path"
                    f" {self.covid_report_path % (str(cases[0].internal_id), ticket_id)}!"
                )
                raise CgError()
            covid_report_path: str = covid_report_options[0]
            covid_destination_path: str = self.covid_destination_path % customer_id
            commands = COVID_RSYNC.format(
                source_path=source_path,
                destination_path=destination_path,
                covid_report_path=covid_report_path,
                covid_destination_path=covid_destination_path,
            )
        else:
            commands = RSYNC_COMMAND.format(
                source_path=source_path, destination_path=destination_path
            )
        error_function = ERROR_RSYNC_FUNCTION.format()
        sbatch_info = {
            "job_name": "_".join([str(ticket_id), "rsync"]),
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
        sbatch_path = log_dir / "_".join([str(ticket_id), "rsync.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
