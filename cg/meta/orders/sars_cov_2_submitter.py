from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import OrderInSample, SarsCov2Sample
from cg.store import models
import datetime as dt


class SarsCov2Submitter(MicrobialSubmitter):
    def validate_order(self, order: OrderIn) -> None:
        super().validate_order(order=order)
        self._validate_sample_names_are_available(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_available(
        self, samples: List[SarsCov2Sample], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: SarsCov2Sample
        for sample in samples:
            sample_name: str = sample.name

            if sample.control:
                continue

            if self.status.find_samples(customer=customer_obj, name=sample_name).first():
                raise OrderError(
                    f"Sample name {sample_name} already in use for customer {customer_obj.name}"
                )

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input for microbial samples."""

        status_data = {
            "customer": order.customer,
            "order": order.name,
            "comment": order.comment,
            "data_analysis": order.samples[0].data_analysis,
            "data_delivery": order.samples[0].data_delivery,
            "samples": [
                {
                    "application": sample.application,
                    "comment": sample.comment,
                    "control": sample.control,
                    "data_delivery": sample.data_delivery,
                    "name": sample.name,
                    "organism_id": sample.organism,
                    "priority": sample.priority,
                    "reference_genome": sample.reference_genome,
                    "volume": sample.volume,
                }
                for sample in order.samples
            ],
        }
        return status_data

    def store_items_in_status(
        self,
        comment: str,
        customer: str,
        data_analysis: Pipeline,
        data_delivery: DataDelivery,
        order: str,
        ordered: dt.datetime,
        items: List[dict],
        ticket: int,
    ) -> [models.Sample]:
        """Store microbial samples in the status database."""

        sample_objs = []

        customer_obj = self.status.customer(customer)
        new_samples = []

        with self.status.session.no_autoflush:

            for sample_data in items:
                case_obj = self.status.find_family(customer=customer_obj, name=ticket)

                if not case_obj:
                    case_obj = self.status.add_case(
                        data_analysis=data_analysis,
                        data_delivery=data_delivery,
                        name=ticket,
                        panels=None,
                    )
                    case_obj.customer = customer_obj
                    self.status.add_commit(case_obj)

                application_tag = sample_data["application"]
                application_version = self.status.current_application_version(application_tag)
                organism = self.status.organism(sample_data["organism_id"])

                if not organism:
                    organism = self.status.add_organism(
                        internal_id=sample_data["organism_id"],
                        name=sample_data["organism_id"],
                        reference_genome=sample_data["reference_genome"],
                    )
                    self.status.add_commit(organism)

                if comment:
                    case_obj.comment = f"Order comment: {comment}"

                new_sample = self.status.add_sample(
                    application_version=application_version,
                    comment=sample_data["comment"],
                    control=sample_data["control"],
                    customer=customer_obj,
                    data_delivery=sample_data["data_delivery"],
                    internal_id=sample_data.get("internal_id"),
                    name=sample_data["name"],
                    order=order,
                    ordered=ordered,
                    organism=organism,
                    priority=sample_data["priority"],
                    reference_genome=sample_data["reference_genome"],
                    sex="unknown",
                    ticket=ticket,
                )

                priority = new_sample.priority
                sample_objs.append(new_sample)
                self.status.relate_sample(family=case_obj, sample=new_sample, status="unknown")
                new_samples.append(new_sample)

            case_obj.priority = priority
            self.status.add_commit(new_samples)
        return sample_objs
