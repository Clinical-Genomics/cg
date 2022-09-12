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
from cg.store import models


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
        self._fill_in_sample_ids(samples, lims_map, id_key="internal_id")
        new_records = self.store_items_in_status(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
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
        self, customer: str, order: str, ordered: dt.datetime, ticket: str, items: List[dict]
    ) -> List[models.Pool]:
        """Store pools in the status database"""
        customer_obj: models.Customer = self.status.customer(customer)
        new_pools: List[models.Pool] = []
        new_samples: List[models.Sample] = []
        for pool in items:
            with self.status.session.no_autoflush:
                application_version: models.ApplicationVersion = (
                    self.status.current_application_version(pool["application"])
                )
            priority: str = pool["priority"]
            case_name: str = self.create_case_name(ticket=ticket, pool_name=pool["name"])
            case_obj: models.Family = self.status.find_family(customer=customer_obj, name=case_name)
            if not case_obj:
                data_analysis: Pipeline = Pipeline(pool["data_analysis"])
                data_delivery: DataDelivery = DataDelivery(pool["data_delivery"])
                case_obj = self.status.add_case(
                    data_analysis=data_analysis,
                    data_delivery=data_delivery,
                    name=case_name,
                    panels=None,
                    priority=priority,
                    ticket=ticket,
                )
                case_obj.customer = customer_obj
                self.status.add_commit(case_obj)

            new_pool: models.Pool = self.status.add_pool(
                application_version=application_version,
                customer=customer_obj,
                name=pool["name"],
                order=order,
                ordered=ordered,
                ticket=ticket,
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
                    original_ticket=ticket,
                    priority=priority,
                    application_version=application_version,
                    customer=customer_obj,
                    no_invoice=True,
                )
                new_samples.append(new_sample)
                self.status.relate_sample(family=case_obj, sample=new_sample, status="unknown")
            new_delivery = self.status.add_delivery(destination="caesar", pool=new_pool)
            self.status.add(new_delivery)
            new_pools.append(new_pool)
        self.status.add_commit(new_pools)

        return new_pools

    def _validate_case_names_are_available(
        self, customer_id: str, samples: List[RmlSample], ticket: str
    ):
        """Validate that the names of all pools are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: RmlSample
        for sample in samples:
            case_name: str = self.create_case_name(pool_name=sample.pool, ticket=ticket)

            if self.status.find_family(customer=customer_obj, name=case_name):
                raise OrderError(
                    f"Case name {case_name} already in use for customer {customer_obj.name}"
                )

    @staticmethod
    def create_case_name(ticket: str, pool_name: str) -> str:
        return f"{ticket}-{pool_name}"
