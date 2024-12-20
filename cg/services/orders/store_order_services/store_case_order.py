import logging
from datetime import datetime

from cg.constants.constants import CaseActions, DataDelivery, Workflow
from cg.constants.pedigree import Pedigree
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.models.sample_aliases import SampleInCase
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.services.orders.submitters.order_submitter import StoreOrderService
from cg.store.models import Case as DbCase
from cg.store.models import CaseSample, Customer
from cg.store.models import Order as DbOrder
from cg.store.models import Sample as DbSample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreCaseOrderService(StoreOrderService):
    """
    Service for storing generic orders in StatusDB and Lims.
    This class is used to store orders for the following workflows:
    - Balsamic
    - Balsamic QC
    - Balsamic UMI
    - MIP DNA
    - MIP RNA
    - Tomte
    """

    def __init__(
        self,
        status_db: Store,
        lims_service: OrderLimsService,
    ):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: OrderWithCases) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        return self._process_case_samples(order=order)

    def _process_case_samples(self, order: OrderWithCases) -> dict:
        """Process samples to be analyzed."""
        project_data = lims_map = None
        if new_samples := [sample for _, _, sample in order.enumerated_new_samples]:
            project_data, lims_map = self.lims.process_lims(
                samples=new_samples,
                customer=order.customer,
                ticket=order._generated_ticket_id,
                order_name=order.name,
                workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
                delivery_type=order.delivery_type,
            )
        if lims_map:
            self._fill_in_sample_ids(samples=new_samples, lims_map=lims_map)

        new_cases: list[DbCase] = self.store_items_in_status(order)
        return {"project": project_data, "records": new_cases}

    def store_items_in_status(self, order: OrderWithCases) -> list[DbCase]:
        """Store cases, samples and their relationship in the Status database."""
        new_cases: list[DbCase] = []
        db_order = self._create_db_order(order)
        for case in order.cases:
            if case.is_new:
                db_case: DbCase = self._create_db_case(
                    case=case,
                    customer=db_order.customer,
                    ticket=str(order._generated_ticket_id),
                    workflow=ORDER_TYPE_WORKFLOW_MAP[order.order_type],
                    delivery_type=order.delivery_type,
                )
                new_cases.append(db_case)
                self._update_case_panel(panels=getattr(case, "panels", []), case=db_case)
                for sample in case.samples:
                    if sample.is_new:
                        db_sample: DbSample = self._create_db_sample(
                            case=case,
                            customer=db_order.customer,
                            order_name=order.name,
                            ordered=datetime.now(),
                            sample=sample,
                            ticket=str(order._generated_ticket_id),
                        )
                    else:
                        db_sample: DbSample = self.status_db.get_sample_by_internal_id(
                            sample.internal_id
                        )

                    sample_mother: SampleInCase = case.get_sample(
                        getattr(sample, Pedigree.MOTHER, None)
                    )
                    sample_father: SampleInCase = case.get_sample(
                        getattr(sample, Pedigree.FATHER, None)
                    )
                    case_sample: CaseSample = self._create_link(
                        case=db_case,
                        db_sample=db_sample,
                        father=sample_father,
                        mother=sample_mother,
                        sample=sample,
                    )

                    self._update_relationship(
                        father=sample_father,
                        link=case_sample,
                        mother=sample_mother,
                        sample=sample,
                    )

            else:
                db_case: DbCase = self._update_existing_case(
                    existing_case=case, ticket_id=order._generated_ticket_id
                )

            db_order.cases.append(db_case)
            self.status_db.session.add_all(new_cases)
            self.status_db.session.add(db_order)
            self.status_db.session.commit()
        return new_cases

    @staticmethod
    def _update_case_panel(panels: list[str], case: DbCase) -> None:
        """Update case panels."""
        case.panels = panels

    @staticmethod
    def _append_ticket(ticket_id: str, case: DbCase) -> None:
        """Add a ticket to the case."""
        case.tickets = f"{case.tickets},{ticket_id}"

    @staticmethod
    def _update_action(action: str, case: DbCase) -> None:
        """Update action of a case."""
        case.action = action

    @staticmethod
    def _update_relationship(
        father: DbSample | None, link: CaseSample, mother: DbSample | None, sample: SampleInCase
    ) -> None:
        link.status = getattr(sample, "status", link.status)
        link.mother = mother or link.mother
        link.father = father or link.father

    def _create_link(
        self,
        case: DbCase,
        db_sample: DbSample,
        father: DbSample,
        mother: DbSample,
        sample: SampleInCase,
    ) -> CaseSample:
        link = self.status_db.relate_sample(
            case=case,
            sample=db_sample,
            status=getattr(sample, "status", None),
            mother=mother,
            father=father,
        )
        self.status_db.session.add(link)
        return link

    def _create_db_sample(
        self,
        case: Case,
        customer: Customer,
        order_name: str,
        ordered: datetime,
        sample: SampleInCase,
        ticket: str,
    ):
        db_sample: DbSample = self.status_db.add_sample(
            internal_id=sample._generated_lims_id,
            order=order_name,
            ordered=ordered,
            original_ticket=ticket,
            priority=case.priority,
            **sample.model_dump(exclude={"application", "container", "container_name"}),
        )
        db_sample.customer = customer
        with self.status_db.session.no_autoflush:
            application_tag = sample.application
            db_sample.application_version = self.status_db.get_current_application_version_by_tag(
                tag=application_tag
            )
        self.status_db.session.add(db_sample)
        return db_sample

    def _create_db_case(
        self,
        case: Case,
        customer: Customer,
        ticket: str,
        workflow: Workflow,
        delivery_type: DataDelivery,
    ) -> DbCase:
        db_case: DbCase = self.status_db.add_case(
            ticket=ticket,
            data_analysis=workflow,
            data_delivery=delivery_type,
            **case.model_dump(exclude={"samples"}),
        )
        db_case.customer = customer
        return db_case

    def _create_db_order(self, order: OrderWithCases) -> DbOrder:
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=order.customer
        )
        return DbOrder(
            customer=customer,
            order_date=datetime.now(),
            ticket_id=order._generated_ticket_id,
        )

    def _update_existing_case(self, existing_case: ExistingCase, ticket_id: int) -> DbCase:
        status_db_case = self.status_db.get_case_by_internal_id(existing_case.internal_id)
        self._append_ticket(ticket_id=ticket_id, case=status_db_case)
        self._update_action(action=CaseActions.ANALYZE, case=status_db_case)
        self._update_case_panel(panels=getattr(existing_case, "panels", []), case=status_db_case)
        return status_db_case
