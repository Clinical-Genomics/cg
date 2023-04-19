import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.models.orders.samples import MetagenomeSample
from cg.store.models import Customer, Family, FamilySample, Sample, ApplicationVersion


class MetagenomeSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        self._validate_sample_names_are_unique(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_unique(
        self, samples: List[MetagenomeSample], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused."""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        for sample in samples:
            if sample.control:
                continue
            if self.status.get_sample_by_customer_and_name(
                customer_entry_id=[customer.id], sample_name=sample.name
            ):
                raise OrderError(f"Sample name {sample.name} already in use")

    def submit_order(self, order: OrderIn) -> dict:
        """Submit a batch of metagenome samples."""
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(samples=status_data["families"][0]["samples"], lims_map=lims_map)
        new_samples = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket_id=order.ticket,
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
        customer_id: str,
        order: str,
        ordered: dt.datetime,
        ticket_id: str,
        items: List[dict],
    ) -> List[Sample]:
        """Store samples in the status database."""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        if customer is None:
            raise OrderError(f"unknown customer: {customer_id}")
        new_samples = []
        case: Family = self.status.get_case_by_name_and_customer(
            customer=customer, case_name=str(ticket_id)
        )
        case_dict: dict = items[0]
        with self.status.session.no_autoflush:
            for sample in case_dict["samples"]:
                new_sample = self.status.add_sample(
                    name=sample["name"],
                    sex="unknown",
                    comment=sample["comment"],
                    control=sample["control"],
                    internal_id=sample.get("internal_id"),
                    order=order,
                    ordered=ordered,
                    original_ticket=ticket_id,
                    priority=sample["priority"],
                )
                new_sample.customer: Customer = customer
                application_tag: str = sample["application"]
                application_version: ApplicationVersion = (
                    self.status.get_current_application_version_by_tag(tag=application_tag)
                )
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version: ApplicationVersion = application_version
                new_samples.append(new_sample)

                if not case:
                    case = self.status.add_case(
                        data_analysis=Pipeline(case_dict["data_analysis"]),
                        data_delivery=DataDelivery(case_dict["data_delivery"]),
                        name=str(ticket_id),
                        panels=None,
                        priority=case_dict["priority"],
                        ticket=ticket_id,
                    )
                    case.customer: Customer = customer
                    self.status.session.add(case)
                    self.status.session.commit()

                new_relationship: FamilySample = self.status.relate_sample(
                    family=case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status.session.add(new_relationship)

        self.status.session.add_all(new_samples)
        self.status.session.commit()
        return new_samples
