import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import MicrobialSample
from cg.store.models import Customer, Family, Organism, Sample, ApplicationVersion


class MicrobialSubmitter(Submitter):
    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input for microbial samples."""

        sample: MicrobialSample
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
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(
            samples=status_data["samples"], lims_map=lims_map, id_key="internal_id"
        )

        # submit samples to Status
        samples = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else dt.datetime.now(),
            ticket_id=order.ticket,
            items=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Pipeline(status_data["data_analysis"]),
            data_delivery=DataDelivery(status_data["data_delivery"]),
        )
        return {"project": project_data, "records": samples}

    def store_items_in_status(
        self,
        comment: str,
        customer_id: str,
        data_analysis: Pipeline,
        data_delivery: DataDelivery,
        order: str,
        ordered: dt.datetime,
        items: List[dict],
        ticket_id: str,
    ) -> [Sample]:
        """Store microbial samples in the status database."""

        sample_objs = []

        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        new_samples = []

        with self.status.session.no_autoflush:
            for sample_data in items:
                case: Family = self.status.get_case_by_name_and_customer(
                    customer=customer, case_name=ticket_id
                )

                if not case:
                    case: Family = self.status.add_case(
                        data_analysis=data_analysis,
                        data_delivery=data_delivery,
                        name=ticket_id,
                        panels=None,
                        ticket=ticket_id,
                    )
                    case.customer: Customer = customer
                    self.status.session.add(case)
                    self.status.session.commit()

                application_tag: str = sample_data["application"]
                application_version: ApplicationVersion = (
                    self.status.get_current_application_version_by_tag(tag=application_tag)
                )
                organism: Organism = self.status.get_organism_by_internal_id(
                    sample_data["organism_id"]
                )

                if not organism:
                    organism: Organism = self.status.add_organism(
                        internal_id=sample_data["organism_id"],
                        name=sample_data["organism_id"],
                        reference_genome=sample_data["reference_genome"],
                    )
                    self.status.session.add(organism)
                    self.status.session.commit()

                if comment:
                    case.comment: str = f"Order comment: {comment}"

                new_sample = self.status.add_sample(
                    name=sample_data["name"],
                    sex="unknown",
                    comment=sample_data["comment"],
                    control=sample_data["control"],
                    internal_id=sample_data.get("internal_id"),
                    order=order,
                    ordered=ordered,
                    original_ticket=ticket_id,
                    priority=sample_data["priority"],
                    application_version=application_version,
                    customer=customer,
                    organism=organism,
                    reference_genome=sample_data["reference_genome"],
                )

                priority = new_sample.priority
                sample_objs.append(new_sample)
                self.status.relate_sample(family=case, sample=new_sample, status="unknown")
                new_samples.append(new_sample)

            case.priority = priority
            self.status.session.add_all(new_samples)
            self.status.session.commit()
        return sample_objs

    def _fill_in_sample_verified_organism(self, samples: List[MicrobialSample]):
        for sample in samples:
            organism_id = sample.organism
            reference_genome = sample.reference_genome
            organism: Organism = self.status.get_organism_by_internal_id(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample.verified_organism = is_verified
