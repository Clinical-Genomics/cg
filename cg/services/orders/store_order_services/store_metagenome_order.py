import logging
from datetime import datetime

from cg.constants import DataDelivery, Sex
from cg.models.orders.sample_base import PriorityEnum, StatusEnum
from cg.services.order_validation_service.workflows.metagenome.models.order import MetagenomeOrder
from cg.services.order_validation_service.workflows.metagenome.models.sample import MetagenomeSample
from cg.services.order_validation_service.workflows.taxprofiler.models.order import TaxprofilerOrder
from cg.services.order_validation_service.workflows.taxprofiler.models.sample import (
    TaxprofilerSample,
)
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion
from cg.store.models import Case as DbCase
from cg.store.models import CaseSample, Customer
from cg.store.models import Order as DbOrder
from cg.store.models import Sample as DbSample
from cg.store.store import Store

LOG = logging.getLogger(__name__)

OrderMetagenome = MetagenomeOrder | TaxprofilerOrder
SampleMetagenome = MetagenomeSample | TaxprofilerSample


class StoreMetagenomeOrderService(StoreOrderService):
    """Storing service for metagenome or Taxprofiler orders."""

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderMetagenome) -> dict:
        """Submit a batch of metagenome samples."""
        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            customer=order.customer,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            delivery_type=DataDelivery(order.delivery_type),
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)
        new_samples = self.store_order_data_in_status_db(order)
        return {"project": project_data, "records": new_samples}

    def store_order_data_in_status_db(
        self,
        order: OrderMetagenome,
    ) -> list[DbSample]:
        """Store samples in the status database."""
        customer: Customer = self.status_db.get_customer_by_internal_id(order.customer)
        new_samples = []
        db_order: DbOrder = self._create_db_order(order)
        priority: PriorityEnum = order.samples[0].priority
        db_case = self._create_db_case(order=order, customer=customer, priority=priority)
        with self.status_db.session.no_autoflush:
            for sample in order.samples:
                db_sample = self._create_db_sample(order=order, sample=sample, customer=customer)
                new_relationship: CaseSample = self.status_db.relate_sample(
                    case=db_case, sample=db_sample, status=StatusEnum.unknown
                )
                self.status_db.session.add(new_relationship)
                new_samples.append(db_sample)
        db_order.cases.append(db_case)
        self.status_db.session.add(db_order)
        self.status_db.session.add_all(new_samples)
        self.status_db.session.commit()
        return new_samples

    def _create_db_order(self, order: OrderMetagenome) -> DbOrder:
        """Return an Order database object."""
        ticket_id: int = order._generated_ticket_id
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        return self.status_db.add_order(customer=customer, ticket_id=ticket_id)

    def _create_db_case(
        self, order: OrderMetagenome, customer: Customer, priority: PriorityEnum
    ) -> DbCase:
        db_case: DbCase = self.status_db.add_case(
            data_analysis=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            data_delivery=DataDelivery(order.delivery_type),
            name=str(order._generated_ticket_id),
            priority=priority,
            ticket=str(order._generated_ticket_id),
        )
        db_case.customer = customer
        self.status_db.session.add(db_case)
        self.status_db.session.commit()
        return db_case

    def _create_db_sample(
        self, sample: SampleMetagenome, order: OrderMetagenome, customer: Customer
    ) -> DbSample:
        db_sample: DbSample = self.status_db.add_sample(
            name=sample.name,
            sex=Sex.UNKNOWN,
            comment=sample.comment,
            control=sample.control,
            order=order.name,
            ordered=datetime.now(),
            original_ticket=order._generated_ticket_id,
            priority=sample.priority,
        )
        db_sample.customer = customer
        application_version: ApplicationVersion = (
            self.status_db.get_current_application_version_by_tag(sample.application)
        )
        db_sample.application_version = application_version
        return db_sample
