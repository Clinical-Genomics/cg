import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.store import models


class PoolSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        pass

    def submit_order(self, order: OrderIn) -> dict:
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
