"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""
import logging
from typing import Optional

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.models.orders.order import OrderIn, OrderType
from cg.store import Store
from .balsamic_submitter import BalsamicSubmitter
from .fastq_submitter import FastqSubmitter
from .fluffy_submitter import FluffySubmitter
from .metagenome_submitter import MetagenomeSubmitter
from .microsalt_submitter import MicrosaltSubmitter
from .mip_dna_submitter import MipDnaSubmitter
from .mip_rna_submitter import MipRnaSubmitter
from .rml_submitter import RmlSubmitter
from .sars_cov_2_submitter import SarsCov2Submitter
from .submitter import Submitter
from .ticket_handler import TicketHandler

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
        OrderType.FLUFFY: FluffySubmitter,
        OrderType.RML: RmlSubmitter,
    }
    if project in submitters:
        return submitters[project](lims=lims, status=status)


class OrdersAPI:
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
        submit_handler.validate_order(order=order_in)

        # detect manual ticket assignment
        ticket_number: Optional[int] = TicketHandler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )

        order_in.ticket = ticket_number
        return submit_handler.submit_order(order=order_in)
