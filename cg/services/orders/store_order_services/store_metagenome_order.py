import logging
from datetime import datetime

from cg.constants import DataDelivery, Sex, Workflow
from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import (
    ApplicationVersion,
    Case,
    CaseSample,
    Customer,
    Order,
    Sample,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreMetagenomeOrderService(StoreOrderService):
    """Storing service for metagenome orders."""

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderIn) -> dict:
        """Submit a batch of metagenome samples."""
        project_data, lims_map = self.lims.process_lims(lims_order=order, new_samples=order.samples)
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(samples=status_data["families"][0]["samples"], lims_map=lims_map)
        new_samples = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket_id=order.ticket,
            items=status_data["families"],
        )
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
        ordered: datetime,
        ticket_id: str,
        items: list[dict],
    ) -> list[Sample]:
        """Store samples in the status database."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        if customer is None:
            raise OrderError(f"unknown customer: {customer_id}")
        new_samples = []
        case: Case = self.status_db.get_case_by_name_and_customer(
            customer=customer, case_name=str(ticket_id)
        )
        case_dict: dict = items[0]
        status_db_order = Order(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=int(ticket_id),
            workflow=Workflow(case_dict["data_analysis"]),
        )
        with self.status_db.session.no_autoflush:
            for sample in case_dict["samples"]:
                new_sample = self.status_db.add_sample(
                    name=sample["name"],
                    sex=Sex.UNKNOWN,
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
                    self.status_db.get_current_application_version_by_tag(tag=application_tag)
                )
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version: ApplicationVersion = application_version
                new_samples.append(new_sample)

                if not case:
                    case = self.status_db.add_case(
                        data_analysis=Workflow(case_dict["data_analysis"]),
                        data_delivery=DataDelivery(case_dict["data_delivery"]),
                        name=str(ticket_id),
                        panels=None,
                        priority=case_dict["priority"],
                        ticket=ticket_id,
                    )
                    case.customer = customer
                    self.status_db.session.add(case)
                    self.status_db.session.commit()

                new_relationship: CaseSample = self.status_db.relate_sample(
                    case=case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status_db.session.add(new_relationship)
        status_db_order.cases.append(case)
        self.status_db.session.add(status_db_order)
        self.status_db.session.add_all(new_samples)
        self.status_db.session.commit()
        return new_samples
