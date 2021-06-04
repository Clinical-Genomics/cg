"""Module for building the rsync command to send files to customer inbox on caesar"""
import datetime
import glob
import logging
import os
from pathlib import Path
from typing import List


from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.utils import Process
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
        self._process = None

    @property
    def process(self):
        if not self._process:
            self._process = Process("rsync")
        return self._process

    def get_source_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()
        customer_id: str = cases[0].customer.internal_id
        delivery_source_path: str = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return delivery_source_path

    def get_destination_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        customer_id: str = cases[0].customer.internal_id
        rsync_destination_path: str = self.destination_path % (customer_id, ticket_id)
        return rsync_destination_path

    def run_rsync_command(self, ticket_id: int = None, dry_run: bool = False) -> None:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        customer_id: str = cases[0].customer.internal_id
        delivery_source_path: str = self.get_source_path(ticket_id=ticket_id)
        rsync_destination_path: str = self.get_destination_path(ticket_id=ticket_id)
        rsync_options = "-rvL"
        parameters: List[str] = [rsync_options, delivery_source_path, rsync_destination_path]
        self.process.run_command(parameters=parameters, dry_run=dry_run)
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
                return
            covid_report_path: str = covid_report_options[0]
            covid_destination_path: str = self.covid_destination_path % customer_id
            parameters: List[str] = [rsync_options, covid_report_path, covid_destination_path]
            self.process.run_command(parameters=parameters, dry_run=dry_run)

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

    def get_account(self) -> str:
        return self.account

    def get_mail_user(self) -> str:
        return self.mail_user
