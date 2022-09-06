import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.models.orders.samples import OrderInSample, MetagenomeSample
from cg.store import models


class MetagenomeSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        self._validate_sample_names_are_unique(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_unique(
        self, samples: List[MetagenomeSample], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: MetagenomeSample
        for sample in samples:
            if sample.control:
                continue
            if self.status.find_samples(customer=customer_obj, name=sample.name).first():
                raise OrderError(f"Sample name {sample.name} already in use")

    def submit_order(self, order: OrderIn) -> dict:
        """Submit a batch of metagenome samples."""
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(status_data["families"][0]["samples"], lims_map)
        new_samples = self.store_items_in_status(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            items=status_data["families"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input to status for metagenome orders."""
        return {
            "customer": order.customer,
            "order": order.name,
            "families": [
                {
                    "data_analysis": order.samples[0].data_analysis,
                    "data_delivery": order.samples[0].data_delivery,
                    "priority": order.samples[0].priority,
                    "samples": [
                        {
                            "application": sample.application,
                            "comment": sample.comment,
                            "control": sample.control,
                            "name": sample.name,
                            "priority": sample.priority,
                            "volume": sample.volume,
                        }
                        for sample in order.samples
                    ],
                }
            ],
        }

    def store_items_in_status(
        self,
        customer: str,
        order: str,
        ordered: dt.datetime,
        ticket: str,
        items: List[dict],
    ) -> List[models.Sample]:
        """Store samples in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_samples = []
        case_obj = self.status.find_family(customer=customer_obj, name=str(ticket))
        case: dict = items[0]
        with self.status.session.no_autoflush:
            for sample in case["samples"]:
                new_sample = self.status.add_sample(
                    name=sample["name"],
                    sex="unknown",
                    comment=sample["comment"],
                    control=sample["control"],
                    internal_id=sample.get("internal_id"),
                    order=order,
                    ordered=ordered,
                    original_ticket=ticket,
                    priority=sample["priority"],
                )
                new_sample.customer = customer_obj
                application_tag = sample["application"]
                application_version = self.status.current_application_version(application_tag)
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version = application_version
                new_samples.append(new_sample)

                if not case_obj:
                    case_obj = self.status.add_case(
                        data_analysis=Pipeline(case["data_analysis"]),
                        data_delivery=DataDelivery(case["data_delivery"]),
                        name=str(ticket),
                        panels=None,
                        priority=case["priority"],
                        ticket=ticket,
                    )
                    case_obj.customer = customer_obj
                    self.status.add(case_obj)

                new_relationship = self.status.relate_sample(
                    family=case_obj, sample=new_sample, status=StatusEnum.unknown
                )
                self.status.add(new_relationship)

        self.status.add_commit(new_samples)
        return new_samples
