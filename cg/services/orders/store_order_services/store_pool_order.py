import logging
from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import SexEnum
from cg.services.order_validation_service.models.sample_aliases import (
    IndexedSample,
    OrderWithIndexedSamples,
)
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

    def store_order(self, order: OrderIn) -> dict:
        status_data = self.order_to_status(order)
        project_data, lims_map = self.lims.process_lims(order=order, new_samples=order.samples)
        samples = [sample for pool in status_data["pools"] for sample in pool["samples"]]
        self._fill_in_sample_ids(samples=samples, lims_map=lims_map, id_key="internal_id")
        new_records = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket_id=order.ticket,
            items=status_data["pools"],
        )
        return {"project": project_data, "records": new_records}

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert input to pools"""

        status_data = {
            "customer": order.customer,
            "order": order.name,
            "comment": order.comment,
            "pools": [],
        }

        # group pools
        pools = {}

        for sample in order.samples:
            pool_name = sample.pool
            application = sample.application
            data_analysis = sample.data_analysis
            data_delivery = sample.data_delivery
            priority = sample.priority

            if pool_name not in pools:
                pools[pool_name] = {}
                pools[pool_name]["name"] = pool_name
                pools[pool_name]["applications"] = set()
                pools[pool_name]["priorities"] = set()
                pools[pool_name]["samples"] = []

            pools[pool_name]["samples"].append(sample)
            pools[pool_name]["applications"].add(application)
            pools[pool_name]["priorities"].add(priority)

        # each pool must only have same of some values
        for pool in pools.values():
            applications = pool["applications"]
            priorities = pool["priorities"]
            pool_name = pool["name"]
            if len(applications) > 1:
                raise OrderError(f"different applications in pool: {pool_name} - {applications}")
            if len(priorities) > 1:
                raise OrderError(f"different priorities in pool: {pool_name} - {priorities}")

        for pool in pools.values():
            pool_name = pool["name"]
            applications = pool["applications"]
            application = applications.pop()
            pool_samples = pool["samples"]
            priorities = pool["priorities"]
            priority = priorities.pop()

            status_data["pools"].append(
                {
                    "name": pool_name,
                    "application": application,
                    "data_analysis": data_analysis,
                    "data_delivery": data_delivery,
                    "priority": priority,
                    "samples": [
                        {
                            "comment": sample.comment,
                            "control": sample.control,
                            "name": sample.name,
                        }
                        for sample in pool_samples
                    ],
                }
            )
        return status_data

    def store_items_in_status(
        self, customer_id: str, order: str, ordered: datetime, ticket_id: str, items: list[dict]
    ) -> list[Pool]:
        """Store pools in the status database."""
        # Create order
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        db_order = Order(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=int(ticket_id),
        )
        new_pools: list[Pool] = []
        new_samples: list[Sample] = []
        for pool in items:
            with self.status_db.session.no_autoflush:
                application_version: ApplicationVersion = (
                    self.status_db.get_current_application_version_by_tag(tag=pool["application"])
                )
            # Create case
            priority: str = pool["priority"]
            case_name: str = self.create_case_name(ticket=ticket_id, pool_name=pool["name"])
            case: Case = self.status_db.get_case_by_name_and_customer(
                customer=db_order.customer, case_name=case_name
            )
            if not case:
                data_analysis: Workflow = Workflow(pool["data_analysis"])
                data_delivery: DataDelivery = DataDelivery(pool["data_delivery"])
                case = self.status_db.add_case(
                    data_analysis=data_analysis,
                    data_delivery=data_delivery,
                    name=case_name,
                    panels=None,
                    priority=priority,
                    ticket=ticket_id,
                )
                case.customer = db_order.customer
                self.status_db.session.add(case)
            # Create Pool
            new_pool: Pool = self.status_db.add_pool(
                application_version=application_version,
                customer=db_order.customer,
                name=pool["name"],
                order=order,
                ordered=ordered,
                ticket=ticket_id,
            )
            # Create samples
            sex: SexEnum = SexEnum.unknown
            for sample in pool["samples"]:
                new_sample = self.status_db.add_sample(
                    name=sample["name"],
                    sex=sex,
                    comment=sample["comment"],
                    control=sample.get("control"),
                    internal_id=sample.get("internal_id"),
                    order=order,
                    ordered=ordered,
                    original_ticket=ticket_id,
                    priority=priority,
                    application_version=application_version,
                    customer=db_order.customer,
                    no_invoice=True,
                )
                new_samples.append(new_sample)
                # Create relationships
                link: CaseSample = self.status_db.relate_sample(
                    case=case, sample=new_sample, status="unknown"
                )
                self.status_db.session.add(link)
            db_order.cases.append(case)
            new_pools.append(new_pool)
        self.status_db.session.add(db_order)
        self.status_db.session.add_all(new_pools)
        self.status_db.session.commit()
        return new_pools

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
        case: Case = self.status_db.get_case_by_name_and_customer(
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

    def _create_pool(self, pool: dict, order_name: str, ticket_id: str, customer: Customer) -> Pool:
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

    @staticmethod
    def create_case_name(ticket: str, pool_name: str) -> str:
        return f"{ticket}-{pool_name}"
