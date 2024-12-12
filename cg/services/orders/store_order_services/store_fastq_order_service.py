import logging
from datetime import datetime

from cg.constants import DataDelivery, GenePanelMasterList, Priority, Workflow
from cg.constants.constants import CustomerId
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.sample_base import StatusEnum
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Order, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreFastqOrderService(StoreOrderService):
    """Storing service for FASTQ orders."""

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: FastqOrder) -> dict:
        """Submit a batch of samples for FASTQ delivery."""

        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            ticket=order.ticket_number,
            order_name=order.name,
            workflow=Workflow.RAW_DATA,
            customer=order.customer,
            delivery_type=DataDelivery(order.delivery_type),
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)
        new_samples = self.store_items_in_status(order=order)
        return {"records": new_samples, "project_data": project_data}

    def create_maf_case(self, sample_obj: Sample, order: Order) -> None:
        """Add a MAF case to the Status database."""
        case: Case = self.status_db.add_case(
            data_analysis=Workflow.MIP_DNA,
            data_delivery=DataDelivery.NO_DELIVERY,
            name="_".join([sample_obj.name, "MAF"]),
            panels=[GenePanelMasterList.OMIM_AUTO],
            priority=Priority.research,
            ticket=sample_obj.original_ticket,
        )
        case.customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=CustomerId.CG_INTERNAL_CUSTOMER
        )
        relationship: CaseSample = self.status_db.relate_sample(
            case=case, sample=sample_obj, status=StatusEnum.unknown
        )
        order.cases.append(case)
        self.status_db.session.add_all([case, relationship])

    def store_items_in_status(self, order: FastqOrder) -> list[Sample]:
        """Store fastq samples in the status database including family connection and delivery"""
        ticket_id: str | None = order.ticket_number
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        new_samples = []
        case: Case = self.status_db.get_case_by_name_and_customer(
            customer=customer, case_name=ticket_id
        )
        status_db_order = Order(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=int(ticket_id),
        )
        with self.status_db.session.no_autoflush:
            for sample in order.samples:
                new_sample = self.status_db.add_sample(
                    name=sample.name,
                    sex=sample.sex or "unknown",
                    comment=sample.comment,
                    internal_id=sample._generated_lims_id,
                    order=order.name,
                    ordered=datetime.now(),
                    original_ticket=ticket_id,
                    priority=sample.priority,
                    tumour=sample.tumour,
                    capture_kit=sample.capture_kit,
                    subject_id=sample.subject_id,
                )
                new_sample.customer = customer
                application_tag: str = sample.application
                application_version: ApplicationVersion = (
                    self.status_db.get_current_application_version_by_tag(application_tag)
                )
                new_sample.application_version = application_version
                new_samples.append(new_sample)
                if not case:
                    case = self.status_db.add_case(
                        data_analysis=Workflow.RAW_DATA,
                        data_delivery=DataDelivery.FASTQ,
                        name=ticket_id,
                        priority=sample.priority,
                        ticket=ticket_id,
                    )
                if (
                    not new_sample.is_tumour
                    and new_sample.prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
                ):
                    self.create_maf_case(sample_obj=new_sample, order=status_db_order)
                case.customer = customer
                new_relationship = self.status_db.relate_sample(
                    case=case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status_db.session.add_all([case, new_relationship])
        status_db_order.cases.append(case)
        self.status_db.session.add(status_db_order)
        self.status_db.session.add_all(new_samples)
        self.status_db.session.commit()
        return new_samples
