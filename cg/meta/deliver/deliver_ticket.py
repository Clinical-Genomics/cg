"""
Module for deliver and rsync customer inbox on the HPC to customer inbox on the delivery server.
"""

import logging
import os
from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.meta.deliver.fastq_path_generator import (
    generate_forward_concatenated_fastq_delivery_path,
    generate_reverse_concatenated_fastq_delivery_path,
)
from cg.store.models import Case

LOG = logging.getLogger(__name__)
PREFIX_TO_CONCATENATE = ["MWG", "MWL", "MWM", "MWR", "MWX"]


class DeliverTicketAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.delivery_path: Path = Path(config.delivery_path)
        self.fastq_concatenation_service = FastqConcatenationService()

    def get_all_cases_from_ticket(self, ticket: str) -> list[Case]:
        return self.status_db.get_cases_by_ticket_id(ticket_id=ticket)

    def get_inbox_path(self, ticket: str) -> Path:
        cases: list[Case] = self.get_all_cases_from_ticket(ticket=ticket)
        if not cases:
            raise CgError(
                f"The customer id was not identified since no cases for ticket {ticket} was found"
            )
        customer_id: str = cases[0].customer.internal_id
        return Path(self.delivery_path, customer_id, INBOX_NAME, ticket)

    def check_if_upload_is_needed(self, ticket: str) -> bool:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)
        LOG.info(f"Checking if path exist: {customer_inbox}")
        if customer_inbox.exists():
            LOG.info(f"Could find path: {customer_inbox}")
            return False
        LOG.info(f"Could not find path: {customer_inbox}")
        return True

    def get_samples_from_ticket(self, ticket: str) -> list[str]:
        all_samples = []
        cases: list[Case] = self.get_all_cases_from_ticket(ticket=ticket)
        for case in cases:
            for link_obj in case.links:
                all_samples.append(link_obj.sample.name)
        return all_samples

    def report_missing_samples(self, ticket: str, dry_run: bool) -> None:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)
        missing_samples = []
        all_samples: list[str] = self.get_samples_from_ticket(ticket=ticket)
        if not customer_inbox.exists() and dry_run:
            LOG.info(f"Dry run, will not search for missing data in: {customer_inbox}")
            return
        if not customer_inbox.exists():
            LOG.info(
                f"The path {customer_inbox} do not exist, no search for missing data will be done"
            )
            return
        for dir_path in customer_inbox.iterdir():
            if len(os.listdir(dir_path)) == 0 and os.path.basename(dir_path) in all_samples:
                missing_samples.append(os.path.basename(dir_path))
        if len(missing_samples) > 0:
            LOG.info("No data delivered for sample(s):")
            for sample in missing_samples:
                LOG.info(sample)
        else:
            LOG.info("Data has been delivered for all samples")

    def concatenate_fastq_files(self, ticket: str, dry_run: bool) -> None:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)

        if not customer_inbox.exists() and dry_run:
            LOG.info(f"Dry run, nothing will be concatenated in: {customer_inbox}")
            return
        if not customer_inbox.exists():
            LOG.info(f"The path {customer_inbox} do not exist, nothing will be concatenated")
            return
        for dir_path in customer_inbox.iterdir():
            if len(os.listdir(dir_path)) == 0:
                LOG.info(f"Empty folder found: {dir_path}")
                continue
            if not dir_path.is_dir():
                continue
            forward_output_path = generate_forward_concatenated_fastq_delivery_path(
                fastq_directory=dir_path, sample_name=dir_path.name
            )
            reverse_output_path = generate_reverse_concatenated_fastq_delivery_path(
                fastq_directory=dir_path, sample_name=dir_path.name
            )
            self.fastq_concatenation_service.concatenate(
                fastq_directory=dir_path,
                forward_output_path=forward_output_path,
                reverse_output_path=reverse_output_path,
                remove_raw=True,
            )
