import logging
from datetime import datetime

from cg.constants import DataDelivery, Sex
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.microsalt.models.sample import MicrosaltSample
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.mutant.models.sample import MutantSample
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
        project_data, lims_map = self.lims.process_lims(
            samples=order.samples,
            customer=order.customer,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            delivery_type=DataDelivery(order.delivery_type),
            skip_reception_control=order.skip_reception_control,
        )
        self._fill_in_sample_ids(samples=order.samples, lims_map=lims_map)

        samples = self.store_order_data_in_status_db(order)
        return {"project": project_data, "records": samples}

    def store_order_data_in_status_db(self, order: MicrobialOrder) -> list[DbSample]:
        """Store microbial samples in the status database."""

        customer: Customer = self.status.get_customer_by_internal_id(order.customer)
        new_samples = []
        db_order: DbOrder = self.status.add_order(
            customer=customer,
            ticket_id=order._generated_ticket_id,
        )
        db_case: DbCase = self._create_case(customer=customer, order=order)

        with self.status.no_autoflush_context():
            for sample in order.samples:
                organism: Organism = self._ensure_organism(sample)
                db_sample = self._create_db_sample(
                    customer=customer,
                    order_name=order.name,
                    organism=organism,
                    sample=sample,
                    ticket_id=order._generated_ticket_id,
                )
                link: CaseSample = self.status.relate_sample(
                    case=db_case, sample=db_sample, status="unknown"
                )
                self.status.add_item_to_store(link)
                new_samples.append(db_sample)
            db_order.cases.append(db_case)

        self.status.add_item_to_store(db_case)
        self.status.add_item_to_store(db_order)
        self.status.add_multiple_items_to_store(new_samples)
        self.status.commit_to_store()
        return new_samples

    def _fill_in_sample_verified_organism(self, samples: list[MicrobialSample]):
        for sample in samples:
            organism_id = sample.organism
            reference_genome = sample.reference_genome
            organism: Organism = self.status.get_organism_by_internal_id(internal_id=organism_id)
            is_verified: bool = (
                organism and organism.reference_genome == reference_genome and organism.verified
            )
            sample._verified_organism = is_verified

    def _create_case(self, customer: Customer, order: MicrobialOrder) -> DbCase:
        case: DbCase = self.status.add_case(
            data_analysis=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
            data_delivery=DataDelivery(order.delivery_type),
            name=str(order._generated_ticket_id),
            panels=None,
            ticket=str(order._generated_ticket_id),
            priority=order.samples[0].priority,
        )
        case.customer = customer
        return case

    def _ensure_organism(self, sample: MicrobialSample) -> Organism:
        organism: Organism = self.status.get_organism_by_internal_id(sample.organism)
        if not organism:
            organism: Organism = self.status.add_organism(
                internal_id=sample.organism,
                name=sample.organism,
                reference_genome=sample.reference_genome,
            )
            self.status.add_item_to_store(organism)
            self.status.commit_to_store()
        return organism

    def _create_db_sample(
        self,
        customer: Customer,
        order_name: str,
        organism: Organism,
        sample: MicrobialSample,
        ticket_id: int,
    ) -> DbSample:
        application_tag: str = sample.application
        application_version: ApplicationVersion = (
            self.status.get_current_application_version_by_tag(tag=application_tag)
        )
        return self.status.add_sample(
            name=sample.name,
            sex=Sex.UNKNOWN,
            comment=sample.comment,
            control=sample.control,
            internal_id=sample._generated_lims_id,
            order=order_name,
            ordered=datetime.now(),
            original_ticket=str(ticket_id),
            priority=sample.priority,
            application_version=application_version,
            customer=customer,
            organism=organism,
            reference_genome=sample.reference_genome,
        )
