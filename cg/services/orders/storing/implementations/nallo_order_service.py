import logging
from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.constants.constants import CaseActions
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.order_types.nallo.models.case import NalloCase
from cg.services.orders.validation.order_types.nallo.models.order import NalloOrder
from cg.services.orders.validation.order_types.nallo.models.sample import NalloSample
from cg.store.models import ApplicationVersion
from cg.store.models import Case as DbCase
from cg.store.models import Customer
from cg.store.models import Order as DbOrder
from cg.store.models import Sample as DbSample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreNalloOrderService(StoreOrderService):
    """
    Service for storing Nallo orders in StatusDB and Lims.
    """

    def __init__(
        self,
        status_db: Store,
        lims_service: OrderLimsService,
    ):
        self.status_db = status_db
        self.lims = lims_service

    def store_order(self, order: NalloOrder) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        new_samples = [sample for _, _, sample in order.enumerated_new_samples]
        project_data, lims_map = self.lims.process_lims(
            samples=new_samples,
            customer=order.customer,
            ticket=order._generated_ticket_id,
            order_name=order.name,
            workflow=Workflow.NALLO,
            delivery_type=order.delivery_type,
            skip_reception_control=order.skip_reception_control,
        )
        self._fill_in_sample_ids(samples=new_samples, lims_map=lims_map)

        new_cases: list[DbCase] = self.store_order_data_in_status_db(order)
        return {"project": project_data, "records": new_cases}

    def store_order_data_in_status_db(self, order: NalloOrder) -> list[DbCase]:
        """Store cases, samples and their relationship in the Status database."""
        new_cases: list[DbCase] = []
        db_order = self._create_db_order(order)
        for case in order.cases:
            if case.is_new:
                db_case: DbCase = self._create_db_case(
                    case=case,
                    customer=db_order.customer,
                    ticket=str(order._generated_ticket_id),
                    delivery_type=order.delivery_type,
                )
                new_cases.append(db_case)
                case_samples: dict[str, DbSample] = self._create_db_sample_dict(
                    case=case, order=order, customer=db_order.customer
                )
                self._create_links(case=case, db_case=db_case, case_samples=case_samples)

            else:
                db_case: DbCase = self._update_existing_case(
                    existing_case=case, ticket_id=order._generated_ticket_id
                )

            db_order.cases.append(db_case)
            self.status_db.add_multiple_items_to_store(new_cases)
            self.status_db.add_item_to_store(db_order)
            self.status_db.commit_to_store()
        return new_cases

    def _create_db_sample(
        self,
        case: NalloCase,
        customer: Customer,
        order_name: str,
        ordered: datetime,
        sample: NalloSample,
        ticket: str,
    ):
        application_tag: str = sample.application
        application_version: ApplicationVersion = (
            self.status_db.get_current_application_version_by_tag(tag=application_tag)
        )
        db_sample: DbSample = self.status_db.add_sample(
            application_version=application_version,
            customer=customer,
            internal_id=sample._generated_lims_id,
            order=order_name,
            ordered=ordered,
            original_ticket=ticket,
            priority=case.priority,
            **sample.model_dump(exclude={"application", "container", "container_name"}),
        )
        return db_sample

    def _create_db_case(
        self,
        case: NalloCase,
        customer: Customer,
        ticket: str,
        delivery_type: DataDelivery,
    ) -> DbCase:
        db_case: DbCase = self.status_db.add_case(
            ticket=ticket,
            data_analysis=Workflow.NALLO,
            data_delivery=delivery_type,
            **case.model_dump(exclude={"samples"}),
        )
        db_case.customer = customer
        return db_case

    def _create_db_order(self, order: NalloOrder) -> DbOrder:
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
        status_db_case.tickets += f",{ticket_id}"
        status_db_case.action = CaseActions.ANALYZE
        status_db_case.panels = existing_case.panels
        return status_db_case

    def _create_links(
        self, case: NalloCase, db_case: DbCase, case_samples: dict[str, DbSample]
    ) -> None:
        """Creates entries in the CaseSample table.
        Input:
        - case: Case, a case within the customer submitted order.
        - db_case: DbCase, Database case entry corresponding to the 'case' parameter.
        - case_samples: dict with keys being sample names in the provided 'case' and values being
        the corresponding database entries in the Sample table."""
        for sample in case.samples:
            if sample.is_new:
                db_sample: DbSample = case_samples.get(sample.name)
            else:
                db_sample: DbSample = self.status_db.get_sample_by_internal_id(sample.internal_id)
            sample_mother_name: str | None = sample.mother
            db_sample_mother: DbSample | None = case_samples.get(sample_mother_name)
            sample_father_name: str = sample.father
            db_sample_father: DbSample | None = case_samples.get(sample_father_name)
            self.status_db.relate_sample(
                case=db_case,
                sample=db_sample,
                status=sample.status,
                mother=db_sample_mother,
                father=db_sample_father,
            )

    def _create_db_sample_dict(
        self, case: NalloCase, order: NalloOrder, customer: Customer
    ) -> dict[str, DbSample]:
        """Constructs a dict containing all the samples in the case. Keys are sample names
        and the values are the database entries for the samples."""
        case_samples: dict[str, DbSample] = {}
        for sample in case.samples:
            if sample.is_new:
                db_sample: DbSample = self._create_db_sample(
                    case=case,
                    customer=customer,
                    order_name=order.name,
                    ordered=datetime.now(),
                    sample=sample,
                    ticket=str(order._generated_ticket_id),
                )
            else:
                db_sample: DbSample = self.status_db.get_sample_by_internal_id(sample.internal_id)
            case_samples[db_sample.name] = db_sample
        return case_samples
