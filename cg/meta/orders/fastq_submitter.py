import datetime as dt

from cg.constants import DataDelivery, GenePanelMasterList
from cg.constants.constants import CustomerId, PrepCategory, Workflow
from cg.constants.priority import Priority
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.store.models import ApplicationVersion, Case, CaseSample, Customer, Sample


class FastqSubmitter(Submitter):
    def submit_order(self, order: OrderIn) -> dict:
        """Submit a batch of samples for FASTQ delivery."""

        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )
        status_data = self.order_to_status(order)
        self._fill_in_sample_ids(samples=status_data["samples"], lims_map=lims_map)
        new_samples = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"],
            ticket_id=order.ticket,
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
                    "subject_id": sample.subject_id,
                    "tumour": sample.tumour,
                    "volume": sample.volume,
                }
                for sample in order.samples
            ],
        }
        return status_data

    def create_maf_case(self, sample_obj: Sample) -> None:
        """Add a MAF case to the Status database."""
        case: Case = self.status.add_case(
            data_analysis=Workflow(Workflow.MIP_DNA),
            data_delivery=DataDelivery(DataDelivery.NO_DELIVERY),
            name="_".join([sample_obj.name, "MAF"]),
            panels=[GenePanelMasterList.OMIM_AUTO],
            priority=Priority.research,
            ticket=sample_obj.original_ticket,
        )
        case.customer = self.status.get_customer_by_internal_id(
            customer_internal_id=CustomerId.CG_INTERNAL_CUSTOMER
        )
        relationship: CaseSample = self.status.relate_sample(
            case=case, sample=sample_obj, status=StatusEnum.unknown
        )
        self.status.session.add_all([case, relationship])

    def store_items_in_status(
        self, customer_id: str, order: str, ordered: dt.datetime, ticket_id: str, items: list[dict]
    ) -> list[Sample]:
        """Store fastq samples in the status database including family connection and delivery"""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        if not customer:
            raise OrderError(f"Unknown customer: {customer_id}")
        new_samples = []
        case: Case = self.status.get_case_by_name_and_customer(
            customer=customer, case_name=ticket_id
        )
        submitted_case: dict = items[0]
        with self.status.session.no_autoflush:
            for sample in items:
                new_sample = self.status.add_sample(
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
                        data_analysis=Workflow(submitted_case["data_analysis"]),
                        data_delivery=DataDelivery(submitted_case["data_delivery"]),
                        name=ticket_id,
                        panels=None,
                        priority=submitted_case["priority"],
                        ticket=ticket_id,
                    )
                if (
                    not new_sample.is_tumour
                    and new_sample.prep_category == PrepCategory.WHOLE_GENOME_SEQUENCING
                ):
                    self.create_maf_case(sample_obj=new_sample)
                case.customer = customer
                new_relationship = self.status.relate_sample(
                    case=case, sample=new_sample, status=StatusEnum.unknown
                )
                self.status.session.add_all([case, new_relationship])

        self.status.session.add_all(new_samples)
        self.status.session.commit()
        return new_samples
