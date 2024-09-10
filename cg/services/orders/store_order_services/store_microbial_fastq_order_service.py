from datetime import datetime

from cg.constants import Workflow, DataDelivery
from cg.models.orders.order import OrderIn

from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.exc import EntryNotFoundError
from cg.store.models import Sample, Customer, Case
from cg.store.store import Store


class StoreMicrobialFastqOrderService(StoreOrderService):

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status = status_db
        self.lims = lims_service

    def store_order(self, order: OrderIn) -> dict:
        project_data, lims_map = self.lims.process_lims(lims_order=order, new_samples=order.samples)
        status_data: dict = self.order_to_status(order)
        self._fill_in_sample_ids(samples=status_data["samples"], lims_map=lims_map)
        new_samples: list[Sample] = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else datetime.now(),
            ticket_id=order.ticket,
            items=status_data["samples"],
        )
        return {"project": project_data, "records": new_samples}

    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input for microbial samples."""
        return {
            "customer": order.customer,
            "order": order.name,
            "samples": [
                {
                    "application": sample.application,
                    "comment": sample.comment,
                    "data_analysis": sample.data_analysis,
                    "data_delivery": sample.data_delivery,
                    "name": sample.name,
                    "priority": sample.priority,
                    "volume": sample.volume,
                    "control": sample.control,
                }
                for sample in order.samples
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
        customer: Customer = self._get_customer(customer_id)
        new_samples: list[Sample] = []
        for sample in items:
            case_name: str = sample["name"]
            case: Case = self._create_case_for_sample(sample, customer, case_name)
            db_sample: Sample = self._create_sample(sample, order, ordered, ticket_id)
            db_sample = self._add_application_to_sample(
                sample=db_sample, application_tag=sample["application"]
            )
            case_sample: CaseSample = self.status.relate_sample(
                case=case, sample=db_sample, status=StatusEnum.unknown
            )
            self.status.add_multiple_items_to_store([case, db_sample, case_sample])
            new_samples.append(db_sample)
        self.status.commit_to_store()
        return new_samples

    def _get_customer(self, customer_id: str) -> Customer:
        if customer := self.status.get_customer_by_internal_id(customer_id):
            return customer
        raise EntryNotFoundError(f"could not find customer: {customer_id}")

    def _create_case_for_sample(self, sample: dict, customer: Customer, case_name: str) -> Case:
        if case := self.status.get_case_by_name_and_customer(
            case_name=case_name, customer=customer
        ):
            return case
        case: Case = self.status.add_case(
            data_analysis=Workflow.FASTQ,
            data_delivery=DataDelivery.FASTQ,
            name=case_name,
            panels=None,
            priority=sample["priority"],
            ticket=case_name,
        )
        case.customer = customer
        return case

    def _create_sample(self, sample_dict: dict, order, ordered, ticket_id: str) -> Sample:
        return self.status.add_sample(
            name=sample_dict["name"],
            sex="unknown",
            comment=sample_dict["comment"],
            internal_id=sample_dict.get("internal_id"),
            order=order,
            ordered=ordered,
            original_ticket=ticket_id,
            priority=sample_dict["priority"],
        )

    def _add_application_to_sample(self, sample: Sample, application_tag: str) -> Sample:
        if application_version := self.status.get_current_application_version_by_tag(
            tag=application_tag
        ):
            sample.application_version = application_version
            return sample
        raise EntryNotFoundError(f"Invalid application: {application_tag}")
