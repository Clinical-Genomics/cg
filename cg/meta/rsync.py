"""Module for building the rsync command to send files to customer inbox on caesar"""
import glob
import logging
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
        self._process = None

    @property
    def process(self):
        if not self._process:
            self._process = Process("rsync")
        return self._process

    def run_rsync_command(self, ticket_id: int = None, dry_run: bool = False) -> None:

        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()

        customer_id: str = cases[0].customer.internal_id
        rsync_destination_path: str = self.destination_path % (customer_id, ticket_id)
        delivery_source_path: str = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
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
