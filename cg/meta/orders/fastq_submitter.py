import datetime as dt
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.store import models


class FastqSubmitter(Submitter):
    def submit_order(self, order: OrderIn) -> dict:
        """Submit a batch of samples for FASTQ delivery."""

        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(status_data["samples"], lims_map)
        new_samples = self.store_items_in_status(
            customer=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket=order.ticket,
            items=status_data["samples"],
        )
        self._add_missing_reads(new_samples)
        return {"project": project_data, "records": new_samples}

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input to status for fastq-only orders."""
        status_data = {
            "customer": order.customer,
            "order": order.name,
            "samples": [
                {
                    "application": sample.application,
                    "capture_kit": sample.capture_kit,
                    "comment": sample.comment,
                    "data_analysis": sample.data_analysis,
                    "data_delivery": sample.data_delivery,
                    "name": sample.name,
                    "priority": sample.priority,
                    "sex": sample.sex,
                    "tumour": sample.tumour,
                    "volume": sample.volume,
                }
                for sample in order.samples
            ],
        }
        return status_data

    @staticmethod
    def _get_fastq_pipeline(
        application_version: models.ApplicationVersion, is_tumour: bool
    ) -> Pipeline:
        if is_tumour:
            return Pipeline.FASTQ
        if application_version.application.prep_category == "wgs":
            return Pipeline.MIP_DNA

        return Pipeline.FASTQ

    def store_items_in_status(
        self, customer: str, order: str, ordered: dt.datetime, ticket: int, items: List[dict]
    ) -> List[models.Sample]:
        """Store fastq samples in the status database including family connection and delivery"""
        production_customer = self.status.customer("cust000")
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_samples = []

        with self.status.session.no_autoflush:
            for sample in items:
                new_sample = self.status.add_sample(
                    capture_kit=sample["capture_kit"],
                    comment=sample["comment"],
                    internal_id=sample.get("internal_id"),
                    name=sample["name"],
                    order=order,
                    ordered=ordered,
                    priority=sample["priority"],
                    sex=sample["sex"] or "unknown",
                    ticket=ticket,
                    tumour=sample["tumour"],
                )
                new_sample.customer = customer_obj
                application_tag = sample["application"]
                application_version = self.status.current_application_version(application_tag)
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version = application_version
                new_samples.append(new_sample)
                data_analysis: Pipeline = self._get_fastq_pipeline(
                    application_version, new_sample.is_tumour
                )
                new_case = self.status.add_case(
                    data_analysis=data_analysis,
                    data_delivery=DataDelivery(sample["data_delivery"]),
                    name=sample["name"],
                    panels=["OMIM-AUTO"],
                    priority="research",
                )
                new_case.customer = production_customer
                self.status.add(new_case)
                new_relationship = self.status.relate_sample(
                    family=new_case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status.add(new_relationship)
                new_delivery = self.status.add_delivery(destination="caesar", sample=new_sample)
                self.status.add(new_delivery)

        self.status.add_commit(new_samples)
        return new_samples
