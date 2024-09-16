import logging
from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StorePacBioOrderService(StoreOrderService):
    """Storing service for PacBio Long Read orders."""

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderIn) -> dict:
        """Submit a batch of samples for PacBio Long Read delivery."""

        project_data, lims_map = self.lims.process_lims(lims_order=order, new_samples=order.samples)
        status_data: dict = self.order_to_status(order)
        self._fill_in_sample_ids(samples=status_data["samples"], lims_map=lims_map)
        new_samples = self._store_samples_in_statusdb(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket_id=order.ticket,
            samples=status_data["samples"],
        )
        return {"project": project_data, "records": new_samples}

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input to status for PacBio-only orders."""
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
                    "subject_id": sample.subject_id,
                    "tumour": sample.tumour,
                    "volume": sample.volume,
                }
                for sample in order.samples
            ],
        }
        return status_data

    def _store_samples_in_statusdb(
        self, customer_id: str, order: str, ordered: datetime, ticket_id: str, samples: list[dict]
    ) -> list[Sample]:
        """Store fastq samples in the status database including family connection and delivery"""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        new_samples = []
        case: Case = self.status_db.get_case_by_name_and_customer(
            customer=customer, case_name=ticket_id
        )
        submitted_case: dict = samples[0]
        with self.status_db.session.no_autoflush:
            for sample in samples:
                new_sample = self.status_db.add_sample(
                    name=sample["name"],
                    sex=sample["sex"] or "unknown",
                    comment=sample["comment"],
                    internal_id=sample.get("internal_id"),
                    order=order,
                    ordered=ordered,
                    original_ticket=ticket_id,
                    priority=sample["priority"],
                    tumour=sample["tumour"],
                    capture_kit=sample["capture_kit"],
                    subject_id=sample["subject_id"],
                )
                new_sample.customer = customer
                application_tag: str = sample["application"]
                application_version: ApplicationVersion = (
                    self.status_db.get_current_application_version_by_tag(tag=application_tag)
                )
                new_sample.application_version = application_version
                new_samples.append(new_sample)
                if not case:
                    case = self.status_db.add_case(
                        data_analysis=Workflow(submitted_case["data_analysis"]),
                        data_delivery=DataDelivery(submitted_case["data_delivery"]),
                        name=ticket_id,
                        panels=None,
                        priority=submitted_case["priority"],
                        ticket=ticket_id,
                    )
                case.customer = customer
                new_relationship: CaseSample = self.status_db.relate_sample(
                    case=case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status_db.session.add_all([case, new_relationship])

        self.status_db.session.add_all(new_samples)
        self.status_db.session.commit()
        return new_samples