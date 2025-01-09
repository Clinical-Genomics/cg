import logging
from datetime import datetime

from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.services.order_validation_service.models.sample_aliases import (
    IndexedSample,
    OrderWithIndexedSamples,
)
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Order, Pool, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StorePoolOrderService(StoreOrderService):
    """
    Service for storing generic orders in StatusDB and Lims.
    This class is used to store orders for the following workflows:
    - Fluffy / NIPT samples
    - RML samples
    """

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderWithIndexedSamples) -> dict:
        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            customer=order.customer,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            delivery_type=order.delivery_type,
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)
        new_records: list[Pool] = self.store_order_data_in_status_db(order=order)
        return {"project": project_data, "records": new_records}

    def store_order_data_in_status_db(self, order: OrderWithIndexedSamples) -> list[Pool]:
        """Store pools in the status database."""
        db_order: Order = self._create_db_order(order=order)
        new_pools: list[Pool] = []
        with self.status_db.no_autoflush_context():
            for pool in order.pools.values():
                db_case: Case = self._create_db_case_for_pool(
                    pool=pool, customer=db_order.customer, ticket_id=str(db_order.ticket_id)
                )
                db_pool: Pool = self._create_db_pool(
                    pool=pool,
                    order_name=order.name,
                    ticket_id=str(db_order.ticket_id),
                    customer=db_order.customer,
                )
                for sample in pool["samples"]:
                    db_sample: Sample = self._create_db_sample(
                        sample=sample,
                        order_name=order.name,
                        ticket_id=str(db_order.ticket_id),
                        customer=db_order.customer,
                        application_version=db_pool.application_version,
                    )
                    case_sample: CaseSample = self.status_db.relate_sample(
                        case=db_case, sample=db_sample, status=StatusEnum.unknown
                    )
                    self.status_db.add_multiple_items_to_store([db_sample, case_sample])
                new_pools.append(db_pool)
                db_order.cases.append(db_case)
                self.status_db.add_multiple_items_to_store([db_pool, db_case])
        self.status_db.add_item_to_store(db_order)
        self.status_db.commit_to_store()
        return new_pools

    @staticmethod
    def create_case_name(ticket: str, pool_name: str) -> str:
        return f"{ticket}-{pool_name}"

    def _create_db_order(self, order: OrderWithIndexedSamples) -> Order:
        """Return an Order database object."""
        ticket_id: int = order._generated_ticket_id
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        return self.status_db.add_order(customer=customer, ticket_id=ticket_id)

    def _create_db_case_for_pool(self, pool: dict, customer: Customer, ticket_id: str) -> Case:
        """Return a Case database object for a pool."""
        case_name: str = self.create_case_name(ticket=ticket_id, pool_name=pool["name"])
        case: Case | None = self.status_db.get_case_by_name_and_customer(
            customer=customer, case_name=case_name
        )
        if not case:
            case = self.status_db.add_case(
                data_analysis=pool["data_analysis"],
                data_delivery=pool["data_delivery"],
                name=case_name,
                priority=pool["priority"],
                ticket=ticket_id,
            )
            case.customer = customer
        return case

    def _create_db_pool(
        self, pool: dict, order_name: str, ticket_id: str, customer: Customer
    ) -> Pool:
        """Return a Pool database object."""
        application_version: ApplicationVersion = (
            self.status_db.get_current_application_version_by_tag(tag=pool["application"])
        )
        return self.status_db.add_pool(
            application_version=application_version,
            customer=customer,
            name=pool["name"],
            order=order_name,
            ordered=datetime.now(),
            ticket=ticket_id,
        )

    def _create_db_sample(
        self,
        sample: IndexedSample,
        order_name: str,
        ticket_id: str,
        customer: Customer,
        application_version: ApplicationVersion,
    ) -> Sample:
        """Return a Sample database object."""
        return self.status_db.add_sample(
            name=sample.name,
            customer=customer,
            application_version=application_version,
            sex=SexEnum.unknown,
            comment=sample.comment,
            control=sample.control,
            internal_id=sample._generated_lims_id,
            order=order_name,
            ordered=datetime.now(),
            original_ticket=ticket_id,
            priority=sample.priority,
            no_invoice=True,
        )
