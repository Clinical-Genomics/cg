import logging
from datetime import datetime

from cg.constants import DataDelivery, Sex, Workflow
from cg.models.orders.order import OrderIn
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import ApplicationVersion
from cg.store.models import Case as DbCase
from cg.store.models import CaseSample, Customer
from cg.store.models import Order as DbOrder
from cg.store.models import Organism
from cg.store.models import Sample as DbSample
from cg.store.store import Store

LOG = logging.getLogger(__name__)

MicrobialOrder = MicrosaltOrder | MutantOrder
MicrobialSample = MicrosaltSample | MutantSample

class StoreMicrobialOrderService(StoreOrderService):
    """
    Storing service for microbial orders.
    These include:
    - Mutant samples
    - Microsalt samples
    """

    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status = status_db
        self.lims = lims_service

    def store_order(self, order: MicrobialOrder) -> dict:
        self._fill_in_sample_verified_organism(order.samples)
        # submit samples to LIMS
        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            customer=order.customer,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            delivery_type=DataDelivery(order.delivery_type),
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)

        # submit samples to Status
        samples = self.store_items_in_status(
            customer_id=status_data["customer"],
            order=status_data["order"],
            ordered=project_data["date"] if project_data else datetime.now(),
            ticket_id=order.ticket,
            items=status_data["samples"],
            comment=status_data["comment"],
            data_analysis=Workflow(status_data["data_analysis"]),
            data_delivery=DataDelivery(status_data["data_delivery"]),
        )
        return {"project": project_data, "records": samples}

    def store_items_in_status(self, order: MicrobialOrder) -> list[DbSample]:
        """Store microbial samples in the status database."""

        sample_objs = []

        customer: Customer = self.status.get_customer_by_internal_id(order.customer)
        new_samples = []
        db_order = DbOrder(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=order._generated_ticket_id,
        )

        with self.status.session.no_autoflush:
            for sample_data in items:
                case: DbCase = self.status.get_case_by_name_and_customer(
                    customer=customer, case_name=ticket_id
                )

                if not case:
                    case: DbCase = self.status.add_case(
                        data_analysis=data_analysis,
                        data_delivery=data_delivery,
                        name=ticket_id,
                        panels=None,
                        ticket=ticket_id,
                    )
                    case.customer = customer
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
                    case.comment = f"Order comment: {comment}"

                new_sample = self.status.add_sample(
                    name=sample_data["name"],
                    sex=Sex.UNKNOWN,
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
                link: CaseSample = self.status.relate_sample(
                    case=case, sample=new_sample, status="unknown"
                )
                self.status.session.add(link)
                new_samples.append(new_sample)

            case.priority = priority
            status_db_order.cases.append(case)
            self.status.session.add(status_db_order)
            self.status.session.add_all(new_samples)
            self.status.session.commit()
        return sample_objs

    def _fill_in_sample_verified_organism(self, samples: list[MicrobialSample]):
        for sample in samples:
            organism_id = sample.organism
            reference_genome = sample.reference_genome
            organism: Organism = self.status.get_organism_by_internal_id(internal_id=organism_id)
            is_verified = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample.verified_organism = is_verified
