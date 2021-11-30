"""Ordering module"""
import datetime as dt
from typing import List, Set

from cg.constants import DataDelivery, Pipeline
from cg.exc import OrderError
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.sample_base import OrderSample, SexEnum, StatusEnum
from cg.models.orders.samples import Of1508Sample, FastqSample
from cg.store import models


class StatusHandler:
    """Handles ordering data for the statusDB"""

    def __init__(self):
        self.status = None

    @staticmethod
    def pools_to_status(order: OrderIn) -> dict:
        """Convert input to pools."""

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
                raise OrderError(f"different application in pool: {pool_name} - {applications}")
            if len(priorities) > 1:
                raise OrderError(f"different priority in pool: {pool_name} - {priorities}")

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

    def store_rml(
        self, customer: str, order: str, ordered: dt.datetime, ticket: int, pools: List[dict]
    ) -> List[models.Pool]:
        """Store pools in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_pools = []
        new_samples = []
        for pool in pools:
            with self.status.session.no_autoflush:
                application_version = self.status.current_application_version(pool["application"])
                if application_version is None:
                    raise OrderError(f"Invalid application: {pool['application']}")

            priority = pool["priority"]
            case_name = f"{ticket}-{pool['name']}"
            case_obj = self.status.find_family(customer=customer_obj, name=case_name)
            if not case_obj:
                data_analysis = Pipeline(pool["data_analysis"])
                data_delivery = DataDelivery(pool["data_delivery"])
                case_obj = self.status.add_case(
                    data_analysis=data_analysis,
                    data_delivery=data_delivery,
                    name=case_name,
                    panels=None,
                    priority=priority,
                )
                case_obj.customer = customer_obj
                self.status.add_commit(case_obj)

            new_pool = self.status.add_pool(
                application_version=application_version,
                customer=customer_obj,
                name=pool["name"],
                order=order,
                ordered=ordered,
                ticket=ticket,
            )
            sex = "unknown"
            for sample in pool["samples"]:
                new_sample = self.status.add_sample(
                    application_version=application_version,
                    comment=sample["comment"],
                    control=sample.get("control"),
                    customer=customer_obj,
                    internal_id=sample.get("internal_id"),
                    name=sample["name"],
                    no_invoice=True,
                    order=order,
                    ordered=ordered,
                    priority=priority,
                    sex=sex,
                    ticket=ticket,
                )
                new_samples.append(new_sample)
                self.status.relate_sample(family=case_obj, sample=new_sample, status="unknown")
            new_delivery = self.status.add_delivery(destination="caesar", pool=new_pool)
            self.status.add(new_delivery)
            new_pools.append(new_pool)
        self.status.add_commit(new_pools)

        return new_pools
