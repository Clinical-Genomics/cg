from datetime import datetime

from cg.constants import DataDelivery, SexOptions, Workflow
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.order_validation_service.workflows.microbial_fastq.models.sample import (
    MicrobialFastqSample,
)
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Order, Sample
from cg.store.store import Store


class StoreMicrobialFastqOrderService(StoreOrderService):

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: MicrobialFastqOrder) -> dict:
        """Store a Microbial FASTQ order in the database."""

        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            ticket=order.ticket_number,
            order_name=order.name,
            workflow=Workflow.RAW_DATA,
            customer=order.customer,
            delivery_type=DataDelivery(order.delivery_type),
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)
        new_samples: list[Sample] = self.store_order_data_in_status_db(order=order)
        return {"records": new_samples, "project_data": project_data}

    # TODO: Remove this method and the tests
    @staticmethod
    def order_to_status(order: OrderIn) -> dict:
        """Convert order input for microbial samples."""
        return {
            "customer": order.customer,
            "order": order.name,
            "comment": order.comment,
            "samples": [
                {
                    "application": sample.application,
                    "comment": sample.comment,
                    "internal_id": sample.internal_id,
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

    def store_order_data_in_status_db(self, order: MicrobialFastqOrder) -> list[Sample]:
        """
        Store order, cases, samples and relationships in the status database. Return the samples.
        """
        db_order = self._create_db_order(order=order)
        new_samples = []
        with self.status_db.session.no_autoflush:
            for sample in order.samples:
                case: Case = self._create_db_case_for_sample(
                    sample=sample, customer=db_order.customer, ticket_id=str(db_order.ticket_id)
                )
                db_sample: Sample = self._create_db_sample(
                    sample=sample,
                    order_name=order.name,
                    ticket_id=str(db_order.ticket_id),
                    customer=db_order.customer,
                )
                case_sample: CaseSample = self.status_db.relate_sample(
                    case=case, sample=db_sample, status=StatusEnum.unknown
                )
                db_order.cases.append(case)
                self.status_db.add_multiple_items_to_store([case, db_sample, case_sample])
                new_samples.append(db_sample)
        self.status_db.add_item_to_store(db_order)
        self.status_db.commit_to_store()
        return new_samples

    def _create_db_case_for_sample(
        self, sample: MicrobialFastqSample, customer: Customer, ticket_id: str
    ) -> Case:
        case_name: str = f"{sample.name}-case"
        case: Case = self.status_db.add_case(
            data_analysis=Workflow.RAW_DATA,
            data_delivery=DataDelivery.FASTQ,
            name=case_name,
            priority=sample.priority,
            ticket=ticket_id,
        )
        case.customer = customer
        return case

    def _create_db_order(self, order: MicrobialFastqOrder) -> Order:
        ticket_id: str = order.ticket_number
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        return self.status_db.add_order(customer=customer, ticket_id=ticket_id)

    def _create_db_sample(
        self,
        sample: MicrobialFastqSample,
        order_name: str,
        ticket_id: str,
        customer: Customer,
    ) -> Sample:
        """Create a sample in the status database."""
        db_sample: Sample = self.status_db.add_sample(
            name=sample.name,
            customer=customer,
            sex=SexOptions.UNKNOWN,
            comment=sample.comment,
            internal_id=sample._generated_lims_id,
            order=order_name,
            ordered=datetime.now(),
            original_ticket=ticket_id,
            priority=sample.priority,
        )
        application_version: ApplicationVersion = (
            self.status_db.get_current_application_version_by_tag(tag=sample.application)
        )
        db_sample.application_version = application_version
        return db_sample
