import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import SexEnum
from cg.models.orders.samples import RmlSample
from cg.store.models import Customer, ApplicationVersion, Pool, Sample, Family


class PoolSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        super().validate_order(order=order)
        self._validate_case_names_are_available(
            customer_id=order.customer, samples=order.samples, ticket=order.ticket
        )

    def submit_order(self, order: OrderIn) -> dict:
        status_data = self.order_to_status(order)
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
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
        self, customer_id: str, order: str, ordered: dt.datetime, ticket_id: str, items: List[dict]
    ) -> List[Pool]:
        """Store pools in the status database."""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        new_pools: List[Pool] = []
        new_samples: List[Sample] = []
        for pool in items:
            with self.status.session.no_autoflush:
                application_version: ApplicationVersion = (
                    self.status.get_current_application_version_by_tag(tag=pool["application"])
                )
            priority: str = pool["priority"]
            case_name: str = self.create_case_name(ticket=ticket_id, pool_name=pool["name"])
            case: Family = self.status.get_case_by_name_and_customer(
                customer=customer, case_name=case_name
            )
            if not case:
                data_analysis: Pipeline = Pipeline(pool["data_analysis"])
                data_delivery: DataDelivery = DataDelivery(pool["data_delivery"])
                case = self.status.add_case(
                    data_analysis=data_analysis,
                    data_delivery=data_delivery,
                    name=case_name,
                    panels=None,
                    priority=priority,
                    ticket=ticket_id,
                )
                case.customer = customer
                self.status.session.add(case)

            new_pool: Pool = self.status.add_pool(
                application_version=application_version,
                customer=customer,
                name=pool["name"],
                order=order,
                ordered=ordered,
                ticket=ticket_id,
            )
            sex: SexEnum = SexEnum.unknown
            for sample in pool["samples"]:
                new_sample = self.status.add_sample(
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
                    customer=customer,
                    no_invoice=True,
                )
                new_samples.append(new_sample)
                self.status.relate_sample(family=case, sample=new_sample, status="unknown")
            new_delivery = self.status.add_delivery(destination="caesar", pool=new_pool)
            self.status.session.add(new_delivery)
            new_pools.append(new_pool)
        self.status.session.add_all(new_pools)
        self.status.session.commit()
        return new_pools

    def _validate_case_names_are_available(
        self, customer_id: str, samples: List[RmlSample], ticket: str
    ):
        """Validate names of all samples are not already in use."""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        for sample in samples:
            case_name: str = self.create_case_name(pool_name=sample.pool, ticket=ticket)
            if self.status.get_case_by_name_and_customer(customer=customer, case_name=case_name):
                raise OrderError(
                    f"Case name {case_name} already in use for customer {customer.name}"
                )

    @staticmethod
    def create_case_name(ticket: str, pool_name: str) -> str:
        return f"{ticket}-{pool_name}"
