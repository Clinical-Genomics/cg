from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.models.orders.samples import MicrobialSample
from cg.store import models
import datetime as dt


class MicrobialSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        pass

    @staticmethod
    def microbial_samples_to_status(order: OrderIn) -> dict:
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

    def submit_order(self, order: OrderIn) -> dict:
        self._fill_in_sample_verified_organism(order.samples)
        # submit samples to LIMS
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        # prepare order for status database
        status_data = self.microbial_samples_to_status(order)
        self._fill_in_sample_ids(status_data["samples"], lims_map, id_key="internal_id")

        # submit samples to Status
        samples = self.store_microbial_samples(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket=order.ticket,
            samples=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Pipeline(status_data["data_analysis"]),
            data_delivery=DataDelivery(status_data["data_delivery"]),
        )
        return {"project": project_data, "records": samples}

    def store_microbial_samples(
        self,
        comment: str,
        customer: str,
        data_analysis: Pipeline,
        data_delivery: DataDelivery,
        order: str,
        ordered: dt.datetime,
        samples: List[dict],
        ticket: int,
    ) -> [models.Sample]:
        """Store microbial samples in the status database."""

        sample_objs = []

        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")

        new_samples = []

        with self.status.session.no_autoflush:

            for sample_data in samples:
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
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample_data['application']}")

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

    def _fill_in_sample_verified_organism(self, samples: List[MicrobialSample]):
        for sample in samples:
            organism_id = sample.organism
            reference_genome = sample.reference_genome
            organism = self.status.organism(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample.verified_organism = is_verified
