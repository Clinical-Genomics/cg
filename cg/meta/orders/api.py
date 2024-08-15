"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

import logging

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.services.orders.store_order_services.store_generic_order import StoreGenericOrderService
from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.store_order_services.store_microbial_order import StoreMicrobialOrderService
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.services.orders.submitters.fastq_order_submitter import FastqOrderSubmitter
from cg.services.orders.submitters.generic_order_submitter import GenericOrderSubmitter
from cg.services.orders.submitters.metagenome_order_submitter import MetagenomeOrderSubmitter
from cg.services.orders.submitters.microbial_order_submitter import MicrobialOrderSubmitter
from cg.services.orders.submitters.order_submitter import (
    OrderSubmitter,
    ValidateOrderService,
    StoreOrderService,
)
from cg.services.orders.submitters.pool_order_submitter import PoolOrderSubmitter
from cg.services.orders.validate_order_services.validate_fastq_order import (
    ValidateFastqOrderService,
)
from cg.services.orders.validate_order_services.validate_generic_order import (
    ValidateGenericOrderService,
)
from cg.services.orders.validate_order_services.validate_metagenome_order import (
    ValidateMetagenomeOrderService,
)
from cg.services.orders.validate_order_services.validate_microbial_order import (
    ValidateMicrobialOrderService,
)
from cg.services.orders.validate_order_services.validate_pool_order import ValidatePoolOrderService
from cg.store.store import Store

LOG = logging.getLogger(__name__)

order_service_mapping = {
    OrderType.BALSAMIC: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.BALSAMIC_QC: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.BALSAMIC_UMI: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.FASTQ: (
        OrderLimsService,
        ValidateFastqOrderService,
        StoreFastqOrderService,
        FastqOrderSubmitter,
    ),
    OrderType.FLUFFY: (
        OrderLimsService,
        ValidatePoolOrderService,
        StorePoolOrderService,
        PoolOrderSubmitter,
    ),
    OrderType.METAGENOME: (
        OrderLimsService,
        ValidateMetagenomeOrderService,
        StoreMetagenomeOrderService,
        MetagenomeOrderSubmitter,
    ),
    OrderType.MICROSALT: (
        OrderLimsService,
        ValidateMicrobialOrderService,
        StoreMicrobialOrderService,
        MicrobialOrderSubmitter,
    ),
    OrderType.MIP_DNA: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.MIP_RNA: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.RML: (
        OrderLimsService,
        ValidatePoolOrderService,
        StorePoolOrderService,
        PoolOrderSubmitter,
    ),
    OrderType.RNAFUSION: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
    OrderType.SARS_COV_2: (
        OrderLimsService,
        ValidateMicrobialOrderService,
        StoreMicrobialOrderService,
        MicrobialOrderSubmitter,
    ),
    OrderType.TOMTE: (
        OrderLimsService,
        ValidateGenericOrderService,
        StoreGenericOrderService,
        GenericOrderSubmitter,
    ),
}


class OrderSubmitterFactory:
    def __init__(self, status_db: Store, lims_api: LimsAPI):
        self.status_db = status_db
        self.lims_api = lims_api

    def create_order_submitter(self, order_type: OrderType) -> OrderSubmitter:
        service_classes = order_service_mapping.get(order_type)

        if not service_classes:
            raise ValueError(f"No services found for order type: {order_type}")

        lims_service, validate_service_class, store_service_class, submitter_class = service_classes

        # Instantiate the necessary services
        lims_service: OrderLimsService = lims_service(self.lims_api)
        validate_service: ValidateOrderService = validate_service_class(self.status_db)
        store_service: StoreOrderService = store_service_class(
            store=self.status_db, lims=lims_service
        )

        # Instantiate and return the corresponding OrderSubmitter
        return submitter_class(
            validate_order_service=validate_service,
            store_order_service=store_service,
        )


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
        submitter_factory = OrderSubmitterFactory(status_db=self.status, lims_api=self.lims)
        submit_handler = submitter_factory.create_order_submitter(order_type=project)

        # detect manual ticket assignment
        ticket_number: str | None = TicketHandler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )
        else:
            self.ticket_handler.connect_to_ticket(
                order=order_in,
                user_name=user_name,
                user_mail=user_mail,
                project=project,
                ticket_number=ticket_number,
            )
        order_in.ticket = ticket_number
        return submit_handler.submit_order(order_in=order_in)
