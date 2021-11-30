"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""
import datetime as dt
import logging
import typing
from typing import List, Optional

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.constants import DataDelivery, Pipeline
from cg.exc import OrderError
from cg.models.orders.order import OrderIn, OrderType
from cg.store import Store, models
from .balsamic_submitter import BalsamicSubmitter
from .fastq_submitter import FastqSubmitter

from .lims import process_lims
from .metagenome_submitter import MetagenomeSubmitter
from .microsalt_submitter import MicrosaltSubmitter
from .mip_dna_submitter import MipDnaSubmitter
from .mip_rna_submitter import MipRnaSubmitter
from .sars_cov_2_submitter import SarsCov2Submitter
from .status import StatusHandler
from .submitter import Submitter
from .ticket_handler import TicketHandler
from ...models.orders.samples import OrderInSample, Of1508Sample, MicrobialSample

LOG = logging.getLogger(__name__)


def _get_submit_handler(project: OrderType, lims: LimsAPI, status: Store) -> Submitter:
    """Factory Method"""

    submitters = {
        OrderType.FASTQ: FastqSubmitter,
        OrderType.METAGENOME: MetagenomeSubmitter,
        OrderType.MICROSALT: MicrosaltSubmitter,
        OrderType.SARS_COV_2: SarsCov2Submitter,
        OrderType.MIP_DNA: MipDnaSubmitter,
        OrderType.BALSAMIC: BalsamicSubmitter,
        OrderType.MIP_RNA: MipRnaSubmitter,
    }
    if project in submitters:
        return submitters[project](lims=lims, status=status)
    return None


class OrdersAPI(StatusHandler):
    """Orders API for accepting new samples into the system."""

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket):
        super().__init__()
        self.lims = lims
        self.status = status
        self.ticket_handler: TicketHandler = TicketHandler(osticket_api=osticket, status_db=status)

    def submit(self, project: OrderType, order_in: OrderIn, user_name: str, user_mail: str) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        submit_handler: Submitter = _get_submit_handler(project, lims=self.lims, status=self.status)
        if submit_handler:
            submit_handler.validate_order(order=order_in)

        # detect manual ticket assignment
        ticket_number: Optional[int] = TicketHandler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )

        order_in.ticket = ticket_number

        if submit_handler:
            return submit_handler.submit_order(order=order_in)

        order_func = self._get_submit_func(project.value)
        return order_func(order_in)

    def _submit_fluffy(self, order: OrderIn) -> dict:
        """Submit a batch of ready made libraries for FLUFFY analysis."""
        return self._submit_pools(order)

    def _submit_rml(self, order: OrderIn) -> dict:
        """Submit a batch of ready made libraries for sequencing."""
        return self._submit_pools(order)

    def _submit_pools(self, order: OrderIn):
        status_data = self.pools_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        samples = [sample for pool in status_data["pools"] for sample in pool["samples"]]
        self._fill_in_sample_ids(samples, lims_map, id_key="internal_id")
        new_records = self.store_rml(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            pools=status_data["pools"],
        )
        return {"project": project_data, "records": new_records}

    def _submit_mip_dna(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order=order, project=OrderType.MIP_DNA)

    def _submit_balsamic(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and balsamic analysis."""
        return self._submit_case_samples(order=order, project=OrderType.BALSAMIC)

    def _submit_mip_rna(self, order: OrderIn) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._submit_case_samples(order=order, project=OrderType.MIP_RNA)

    def _add_missing_reads(self, samples: List[models.Sample]):
        """Add expected reads/reads missing."""
        for sample_obj in samples:
            LOG.info(f"{sample_obj.internal_id}: add missing reads in LIMS")
            target_reads = sample_obj.application_version.application.target_reads / 1000000
            self.lims.update_sample(sample_obj.internal_id, target_reads=target_reads)

    @staticmethod
    def _fill_in_sample_ids(samples: List[dict], lims_map: dict, id_key: str = "internal_id"):
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample['name']}: link sample to LIMS")
            if not sample.get(id_key):
                internal_id = lims_map[sample["name"]]
                LOG.info(f"{sample['name']} -> {internal_id}: connect sample to LIMS")
                sample[id_key] = internal_id

    def _get_submit_func(self, project_type: OrderType) -> typing.Callable:
        """Get the submit method to call for the given type of project"""

        if project_type == OrderType.MIP_DNA:
            return getattr(self, "_submit_mip_dna")
        if project_type == OrderType.MIP_RNA:
            return getattr(self, "_submit_mip_rna")
        if project_type == OrderType.SARS_COV_2:
            return getattr(self, "_submit_sars_cov_2")

        return getattr(self, f"_submit_{str(project_type)}")
