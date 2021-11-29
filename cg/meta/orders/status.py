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
    def group_cases(samples: List[Of1508Sample]) -> dict:
        """Group samples in cases."""
        cases = {}
        for sample in samples:
            case_id = sample.family_name
            if case_id not in cases:
                cases[case_id] = []
            cases[case_id].append(sample)
        return cases

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

    @classmethod
    def cases_to_status(cls, order: OrderIn, project: OrderType) -> dict:
        """Convert order input to status interface input."""
        status_data = {"customer": order.customer, "order": order.name, "families": []}
        cases = cls.group_cases(order.samples)

        for case_name, case_samples in cases.items():

            cohorts: Set[str] = {
                cohort for sample in case_samples for cohort in sample.cohorts if cohort
            }
            synopsis: str = ", ".join(set(sample.synopsis or "" for sample in case_samples))

            case_internal_id: str = cls.get_single_value(
                case_name, case_samples, "case_internal_id"
            )
            data_analysis = cls.get_single_value(case_name, case_samples, "data_analysis")
            data_delivery = cls.get_single_value(case_name, case_samples, "data_delivery")
            priority = cls.get_single_value(case_name, case_samples, "priority", "standard")

            panels: Set[str] = set()
            if project == OrderType.MIP_DNA:
                panels: Set[str] = {
                    panel for sample in case_samples for panel in sample.panels if panel
                }

            case = {
                # Set from first sample until order portal sets this on case level
                "cohorts": cohorts,
                "data_analysis": data_analysis,
                "data_delivery": data_delivery,
                "name": case_name,
                "internal_id": case_internal_id,
                "priority": priority,
                "panels": list(panels),
                "samples": [
                    {
                        "age_at_sampling": sample.age_at_sampling,
                        "application": sample.application,
                        "capture_kit": sample.capture_kit,
                        "comment": sample.comment,
                        "father": sample.father,
                        "internal_id": sample.internal_id,
                        "mother": sample.mother,
                        "name": sample.name,
                        "phenotype_groups": list(sample.phenotype_groups),
                        "phenotype_terms": list(sample.phenotype_terms),
                        "sex": sample.sex,
                        "status": sample.status,
                        "subject_id": sample.subject_id,
                        "time_point": sample.time_point if hasattr(sample, "time_point") else None,
                        "tumour": sample.tumour,
                    }
                    for sample in case_samples
                ],
                "synopsis": synopsis,
            }

            status_data["families"].append(case)
        return status_data

    @classmethod
    def get_single_value(cls, case_name, case_samples, value_key, value_default=None):
        values = set(getattr(sample, value_key) or value_default for sample in case_samples)
        if len(values) > 1:
            raise ValueError(f"different sample {value_key} values: {case_name} - {values}")
        single_value = values.pop()
        return single_value

    def store_cases(
        self, customer: str, order: str, ordered: dt.datetime, ticket: int, cases: List[dict]
    ) -> List[models.Family]:
        """Store cases and samples in the status database."""

        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"Unknown customer: {customer}")
        new_families = []
        for case in cases:
            case_obj = self.status.family(case["internal_id"])
            if case_obj:
                case_obj.panels = case["panels"]
            else:
                case_obj = self.status.add_case(
                    cohorts=case["cohorts"],
                    data_analysis=Pipeline(case["data_analysis"]),
                    data_delivery=DataDelivery(case["data_delivery"]),
                    name=case["name"],
                    panels=case["panels"],
                    priority=case["priority"],
                    synopsis=case["synopsis"],
                )
                case_obj.customer = customer_obj
                new_families.append(case_obj)

            family_samples = {}
            for sample in case["samples"]:
                sample_obj = self.status.sample(sample["internal_id"])
                if sample_obj:
                    family_samples[sample["name"]] = sample_obj
                else:
                    new_sample = self.status.add_sample(
                        age_at_sampling=sample["age_at_sampling"],
                        capture_kit=sample["capture_kit"],
                        comment=sample["comment"],
                        internal_id=sample["internal_id"],
                        name=sample["name"],
                        order=order,
                        ordered=ordered,
                        phenotype_groups=sample["phenotype_groups"],
                        phenotype_terms=sample["phenotype_terms"],
                        priority=case["priority"],
                        sex=sample["sex"],
                        subject_id=sample["subject_id"],
                        ticket=ticket,
                        time_point=sample["time_point"],
                        tumour=sample["tumour"],
                    )
                    new_sample.customer = customer_obj
                    with self.status.session.no_autoflush:
                        application_tag = sample["application"]
                        new_sample.application_version = self.status.current_application_version(
                            application_tag
                        )
                    if new_sample.application_version is None:
                        raise OrderError(f"Invalid application: {sample['application']}")

                    family_samples[new_sample.name] = new_sample
                    self.status.add(new_sample)
                    new_delivery = self.status.add_delivery(destination="caesar", sample=new_sample)
                    self.status.add(new_delivery)

            for sample in case["samples"]:
                mother_obj = family_samples.get(sample["mother"]) if sample.get("mother") else None
                father_obj = family_samples.get(sample["father"]) if sample.get("father") else None
                with self.status.session.no_autoflush:
                    link_obj = self.status.link(case_obj.internal_id, sample["internal_id"])
                if link_obj:
                    link_obj.status = sample["status"] or link_obj.status
                    link_obj.mother = mother_obj or link_obj.mother
                    link_obj.father = father_obj or link_obj.father
                else:
                    new_link = self.status.relate_sample(
                        family=case_obj,
                        sample=family_samples[sample["name"]],
                        status=sample["status"],
                        mother=mother_obj,
                        father=father_obj,
                    )
                    self.status.add(new_link)
            self.status.add_commit(new_families)
        return new_families

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
