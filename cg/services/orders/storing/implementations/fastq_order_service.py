import logging
from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.fastq.models.sample import FastqSample
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Order, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreFastqOrderService(StoreOrderService):
    """Storing service for FASTQ orders."""

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: FastqOrder) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=Workflow.RAW_DATA,
            customer=order.customer,
            delivery_type=DataDelivery(order.delivery_type),
            skip_reception_control=order.skip_reception_control,
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)
        new_samples: list[Sample] = self.store_order_data_in_status_db(order=order)
        return {"records": new_samples, "project": project_data}

    def store_order_data_in_status_db(self, order: FastqOrder) -> list[Sample]:
        """
        Store all order data in the Status database for a FASTQ order. Return the samples.
        The stored data objects are:
        - Order
        - Samples
        - One Case per sample
        - For each Sample, a relationship between the sample and its Case
        """
        db_order: Order = self._create_db_order(order=order)
        new_samples = []
        with self.status_db.session.no_autoflush:
            for sample in order.samples:
                db_case: Case = self._create_db_case_for_sample(
                    sample=sample, customer=db_order.customer, order=order
                )
                db_sample: Sample = self._create_db_sample(
                    sample=sample,
                    order_name=order.name,
                    ticket_id=str(db_order.ticket_id),
                    customer=db_order.customer,
                )
                case_sample: CaseSample = self.status_db.relate_sample(
                    case=db_case, sample=db_sample, status=StatusEnum.unknown
                )
                self.status_db.add_multiple_items_to_store([db_sample, case_sample, db_case])
                new_samples.append(db_sample)
                db_order.cases.append(db_case)
        self.status_db.add_item_to_store(db_order)
        self.status_db.commit_to_store()
        return new_samples

    def _create_db_order(self, order: FastqOrder) -> Order:
        """Return an Order database object."""
        ticket_id: int = order._generated_ticket_id
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        return self.status_db.add_order(customer=customer, ticket_id=ticket_id)

    def _create_db_case_for_sample(
        self,
        sample: FastqSample,
        customer: Customer,
        order: FastqOrder,
    ) -> Case:
        """Return a Case database object."""
        ticket_id = str(order._generated_ticket_id)
        case_name: str = f"{sample.name}-{ticket_id}"
        priority: str = sample.priority
        case: Case = self.status_db.add_case(
            data_analysis=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            data_delivery=DataDelivery(order.delivery_type),
            name=case_name,
            priority=priority,
            ticket=ticket_id,
        )
        case.customer = customer
        return case

    def _create_db_sample(
        self, sample: FastqSample, order_name: str, customer: Customer, ticket_id: str
    ) -> Sample:
        """Return a Sample database object."""
        application_version: ApplicationVersion = (
            self.status_db.get_current_application_version_by_tag(tag=sample.application)
        )
        return self.status_db.add_sample(
            name=sample.name,
            sex=sample.sex or SexEnum.unknown,
            comment=sample.comment,
            internal_id=sample._generated_lims_id,
            ordered=datetime.now(),
            original_ticket=ticket_id,
            priority=sample.priority,
            tumour=sample.tumour,
            capture_kit=sample.capture_kit,
            subject_id=sample.subject_id,
            customer=customer,
            application_version=application_version,
            order=order_name,
        )
