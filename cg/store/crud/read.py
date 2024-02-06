"""Handler to read data objects."""

import datetime as dt
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Callable, Iterator, Literal

from sqlalchemy.orm import Query, Session

from cg.constants import FlowCellStatus, Workflow
from cg.constants.constants import CaseActions, CustomerId, PrepCategory, SampleType
from cg.exc import CaseNotFoundError, CgError
from cg.store.base import BaseHandler
from cg.store.filters.status_analysis_filters import (
    AnalysisFilter,
    apply_analysis_filter,
)
from cg.store.filters.status_application_filters import (
    ApplicationFilter,
    apply_application_filter,
)
from cg.store.filters.status_application_limitations_filters import (
    ApplicationLimitationsFilter,
    apply_application_limitations_filter,
)
from cg.store.filters.status_application_version_filters import (
    ApplicationVersionFilter,
    apply_application_versions_filter,
)
from cg.store.filters.status_bed_filters import BedFilter, apply_bed_filter
from cg.store.filters.status_bed_version_filters import (
    BedVersionFilter,
    apply_bed_version_filter,
)
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_case_sample_filters import (
    CaseSampleFilter,
    apply_case_sample_filter,
)
from cg.store.filters.status_collaboration_filters import (
    CollaborationFilter,
    apply_collaboration_filter,
)
from cg.store.filters.status_customer_filters import (
    CustomerFilter,
    apply_customer_filter,
)
from cg.store.filters.status_flow_cell_filters import (
    FlowCellFilter,
    apply_flow_cell_filter,
)
from cg.store.filters.status_invoice_filters import InvoiceFilter, apply_invoice_filter
from cg.store.filters.status_metrics_filters import (
    SequencingMetricsFilter,
    apply_metrics_filter,
)
from cg.store.filters.status_order_filters import OrderFilter, apply_order_filters
from cg.store.filters.status_organism_filters import (
    OrganismFilter,
    apply_organism_filter,
)
from cg.store.filters.status_panel_filters import PanelFilter, apply_panel_filter
from cg.store.filters.status_pool_filters import PoolFilter, apply_pool_filter
from cg.store.filters.status_sample_filters import SampleFilter, apply_sample_filter
from cg.store.filters.status_user_filters import UserFilter, apply_user_filter
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Bed,
    BedVersion,
    Case,
    CaseSample,
    Collaboration,
    Customer,
    Flowcell,
    Invoice,
    Order,
    Organism,
    Panel,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
    User,
)

LOG = logging.getLogger(__name__)


class ReadHandler(BaseHandler):
    """Class for reading items in the database."""

    def __init__(self, session: Session):
        super().__init__(session=session)

    def get_case_by_entry_id(self, entry_id: str) -> Case:
        """Return a case by entry id."""
        cases_query: Query = self._get_query(table=Case)
        return apply_case_filter(
            cases=cases_query, filter_functions=[CaseFilter.FILTER_BY_ENTRY_ID], entry_id=entry_id
        ).first()

    def has_active_cases_for_sample(self, internal_id: str) -> bool:
        """Check if there are any active cases for a sample."""
        sample = self.get_sample_by_internal_id(internal_id=internal_id)
        active_actions = ["analyze", "running"]

        for family_sample in sample.links:
            case: Case = self.get_case_by_entry_id(entry_id=family_sample.case_id)
            if case.action in active_actions:
                return True

        return False

    def get_application_by_case(self, case_id: str) -> Application:
        """Return the application of a case."""

        return (
            self.get_case_by_internal_id(internal_id=case_id)
            .links[0]
            .sample.application_version.application
        )

    def get_application_limitations_by_tag(self, tag: str) -> list[ApplicationLimitations] | None:
        """Return application limitations given the application tag."""
        return apply_application_limitations_filter(
            filter_functions=[ApplicationLimitationsFilter.FILTER_BY_TAG],
            application_limitations=self._get_join_application_limitations_query(),
            tag=tag,
        ).all()

    def get_application_limitation_by_tag_and_workflow(
        self, tag: str, workflow: Workflow
    ) -> ApplicationLimitations | None:
        """Return an application limitation given the application tag and workflow."""
        filter_functions: list[ApplicationLimitationsFilter] = [
            ApplicationLimitationsFilter.FILTER_BY_TAG,
            ApplicationLimitationsFilter.FILTER_BY_WORKFLOW,
        ]
        return apply_application_limitations_filter(
            filter_functions=filter_functions,
            application_limitations=self._get_join_application_limitations_query(),
            tag=tag,
            workflow=workflow,
        ).first()

    def get_latest_analysis_to_upload_for_workflow(self, workflow: str = None) -> list[Analysis]:
        """Return latest not uploaded analysis for each case given a workflow."""
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_WITH_WORKFLOW,
            AnalysisFilter.FILTER_IS_NOT_UPLOADED,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_latest_analyses_for_cases_query(),
            workflow=workflow,
        ).all()

    def get_analysis_by_case_entry_id_and_started_at(
        self, case_entry_id: int, started_at_date: dt.datetime
    ) -> Analysis:
        """Fetch an analysis."""
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_BY_CASE_ENTRY_ID,
            AnalysisFilter.FILTER_BY_STARTED_AT,
        ]

        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_query(Analysis),
            case_entry_id=case_entry_id,
            started_at_date=started_at_date,
        ).first()

    def get_cases_by_customer_and_case_name_search(
        self, customer: Customer, case_name_search: str
    ) -> list[Case]:
        """
        Retrieve a list of cases filtered by a customer and matching names.

        Args:
            customer (Customer): The customer object to filter cases by.
            case_name_search (str): The case name search string to filter cases by.

        Returns:
            list[Case]: A list of filtered cases sorted by creation time.
        """
        filter_functions: list[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID,
            CaseFilter.FILTER_BY_NAME_SEARCH,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=filter_functions,
            customer_entry_id=customer.id,
            name_search=case_name_search,
        ).all()

    def get_cases_by_customers_action_and_case_search(
        self,
        customers: list[Customer] | None,
        action: str | None,
        case_search: str | None,
        limit: int | None = 30,
    ) -> list[Case]:
        """
        Retrieve a list of cases filtered by customers, action, and matching names or internal ids.

        Args:
            customers (list[Customer] | None): A list of customer objects to filter cases by.
            action (str | None): The action string to filter cases by.
            case_search (str | None): The case search string to filter cases by.
            limit (int | None, default=30): The maximum number of cases to return.

        Returns:
            list[Case]: A list of filtered cases sorted by creation time and limited by the specified number.
        """
        filter_functions: list[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_IDS,
            CaseFilter.FILTER_BY_ACTION,
            CaseFilter.FILTER_BY_CASE_SEARCH,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        customer_entry_ids: list[int] = (
            [customer.id for customer in customers] if customers else None
        )

        filtered_cases: Query = apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=filter_functions,
            action=action,
            case_search=case_search,
            customer_entry_ids=customer_entry_ids,
        )
        return filtered_cases.limit(limit=limit).all()

    def get_cases_by_customer_workflow_and_case_search(
        self,
        customer: Customer | None,
        workflow: str | None,
        case_search: str | None,
        limit: int | None = 30,
    ) -> list[Case]:
        """
        Retrieve a list of cases filtered by customer, workflow, and matching names or internal ids.
        """
        filter_functions: list[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID,
            CaseFilter.FILTER_BY_CASE_SEARCH,
            CaseFilter.FILTER_WITH_WORKFLOW,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        customer_entry_id: int = customer.id if customer else None

        filtered_cases: Query = apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=filter_functions,
            case_search=case_search,
            customer_entry_id=customer_entry_id,
            workflow=workflow,
        )
        return filtered_cases.limit(limit=limit).all()

    def get_cases(self) -> list[Case]:
        """Return all cases."""
        return self._get_query(table=Case).all()

    def get_case_samples_by_case_id(self, case_internal_id: str) -> list[CaseSample]:
        """Return the case-sample links associated with a case."""
        return apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_SAMPLES_IN_CASE_BY_INTERNAL_ID],
            case_internal_id=case_internal_id,
            case_samples=self._get_join_case_sample_query(),
        ).all()

    def filter_cases_with_samples(self, case_ids: list[str]) -> list[str]:
        """Return case id:s associated with samples."""
        cases_with_samples = set()
        for case_id in case_ids:
            case: Case = self.get_case_by_internal_id(internal_id=case_id)
            if case and case.links:
                cases_with_samples.add(case_id)
        return list(cases_with_samples)

    def get_cases_by_ticket_id(self, ticket_id: str) -> list[Case]:
        """Return cases associated with a given ticket id."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket_id,
        ).all()

    def get_customer_id_from_ticket(self, ticket: str) -> str:
        """Returns the customer related to given ticket."""
        cases: list[Case] = self.get_cases_by_ticket_id(ticket_id=ticket)
        if not cases:
            raise ValueError(f"No case found for ticket {ticket}")
        return cases[0].customer.internal_id

    def get_samples_from_ticket(self, ticket: str) -> list[Sample]:
        """Returns the samples related to given ticket."""
        return apply_case_filter(
            cases=self._get_join_sample_family_query(),
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket,
        ).all()

    def get_latest_ticket_from_case(self, case_id: str) -> str:
        """Returns the ticket from the most recent sample in a case."""
        return self.get_case_by_internal_id(internal_id=case_id).latest_ticket

    def get_latest_flow_cell_on_case(self, family_id: str) -> Flowcell:
        """Fetch the latest sequenced flow cell related to a sample on a case."""
        flow_cells_on_case: list[Flowcell] = self.get_flow_cells_by_case(
            case=self.get_case_by_internal_id(internal_id=family_id)
        )
        flow_cells_on_case.sort(key=lambda flow_cell: flow_cell.sequenced_at)
        return flow_cells_on_case[-1] if flow_cells_on_case else None

    def _is_case_found(self, case: Case, case_id: str) -> None:
        """Raise error if case is false."""
        if not case:
            LOG.error(f"Could not find case {case_id}")
            raise CaseNotFoundError("")

    def get_samples_by_case_id(self, case_id: str) -> list[Sample]:
        """Get samples on a given case id."""

        case: Case = self.get_case_by_internal_id(internal_id=case_id)
        self._is_case_found(case=case, case_id=case_id)
        return case.samples if case else []

    def get_sample_ids_by_case_id(self, case_id: str = None) -> Iterator[str]:
        """Return sample ids from case id."""
        case: Case = self.get_case_by_internal_id(internal_id=case_id)
        self._is_case_found(case=case, case_id=case_id)
        for link in case.links:
            yield link.sample.internal_id

    def get_case_by_name_and_customer(self, customer: Customer, case_name: str) -> Case:
        """Find a case by case name within a customer."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID, CaseFilter.FILTER_BY_NAME],
            customer_entry_id=customer.id,
            name=case_name,
        ).first()

    def get_case_by_name(self, name: str) -> Case:
        """Get a case by name."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.FILTER_BY_NAME],
            name=name,
        ).first()

    def get_sample_by_customer_and_name(
        self, customer_entry_id: list[int], sample_name: str
    ) -> Sample:
        """Get samples within a customer."""
        filter_functions = [
            SampleFilter.FILTER_BY_CUSTOMER_ENTRY_IDS,
            SampleFilter.FILTER_BY_SAMPLE_NAME,
        ]

        return apply_sample_filter(
            samples=self._get_query(table=Sample),
            filter_functions=filter_functions,
            customer_entry_ids=customer_entry_id,
            name=sample_name,
        ).first()

    def get_number_of_reads_for_sample_passing_q30_threshold(
        self, sample_internal_id: str, q30_threshold: int
    ) -> int:
        """Get number of reads above q30 threshold for sample from sample lane sequencing metrics."""
        total_reads_query: Query = apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[
                SequencingMetricsFilter.FILTER_TOTAL_READ_COUNT_FOR_SAMPLE,
                SequencingMetricsFilter.FILTER_ABOVE_Q30_THRESHOLD,
            ],
            sample_internal_id=sample_internal_id,
            q30_threshold=q30_threshold,
        )
        reads_count: int | None = total_reads_query.scalar()
        return reads_count if reads_count else 0

    def get_average_q30_for_sample_on_flow_cell(
        self, sample_internal_id: str, flow_cell_name: str
    ) -> float:
        """Calculates the average q30 across lanes for a sample on a flow cell."""
        sample_lanes: list[SampleLaneSequencingMetrics] = apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[
                SequencingMetricsFilter.FILTER_BY_FLOW_CELL_NAME,
                SequencingMetricsFilter.FILTER_BY_SAMPLE_INTERNAL_ID,
            ],
            sample_internal_id=sample_internal_id,
            flow_cell_name=flow_cell_name,
        ).all()

        return sum(
            [sample_lane.sample_base_percentage_passing_q30 for sample_lane in sample_lanes]
        ) / len(sample_lanes)

    def get_average_percentage_passing_q30_for_flow_cell(self, flow_cell_name: str) -> float:
        """Calculates the average q30 for each sample on a flow cell and returns the average between the samples."""
        sequencing_metrics: list[SampleLaneSequencingMetrics] = (
            self.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name=flow_cell_name)
        )
        unique_sample_internal_ids: set[str] = {
            sequencing_metric.sample_internal_id for sequencing_metric in sequencing_metrics
        }

        sum_average_q30_across_samples: float = 0
        for sample_internal_id in unique_sample_internal_ids:
            sum_average_q30_across_samples += self.get_average_q30_for_sample_on_flow_cell(
                sample_internal_id=sample_internal_id,
                flow_cell_name=flow_cell_name,
            )
        return (
            sum_average_q30_across_samples / len(unique_sample_internal_ids)
            if sum_average_q30_across_samples and unique_sample_internal_ids
            else 0
        )

    def get_number_of_reads_for_flow_cell(self, flow_cell_name: str) -> int:
        """Get total number of reads for a flow cell from sample lane sequencing metrics."""
        sequencing_metrics: list[SampleLaneSequencingMetrics] = (
            self.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name=flow_cell_name)
        )
        read_count: int = 0
        for sequencing_metric in sequencing_metrics:
            read_count += sequencing_metric.sample_total_reads_in_lane
        return read_count

    def get_sample_lane_sequencing_metrics_by_flow_cell_name(
        self, flow_cell_name: str
    ) -> list[SampleLaneSequencingMetrics]:
        """Return sample lane sequencing metrics for a flow cell."""
        return apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[SequencingMetricsFilter.FILTER_BY_FLOW_CELL_NAME],
            flow_cell_name=flow_cell_name,
        ).all()

    def get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        self, flow_cell_name: str, sample_internal_id: str, lane: int
    ) -> SampleLaneSequencingMetrics:
        """Get metrics entry by flow cell name, sample internal id and lane."""
        return apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[
                SequencingMetricsFilter.FILTER_BY_FLOW_CELL_SAMPLE_INTERNAL_ID_AND_LANE
            ],
            flow_cell_name=flow_cell_name,
            sample_internal_id=sample_internal_id,
            lane=lane,
        ).first()

    def get_flow_cell_by_name(self, flow_cell_name: str) -> Flowcell | None:
        """Return flow cell by flow cell name."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_name=flow_cell_name,
            filter_functions=[FlowCellFilter.FILTER_BY_NAME],
        ).first()

    def get_flow_cells_by_statuses(self, flow_cell_statuses: list[str]) -> list[Flowcell] | None:
        """Return flow cells with supplied statuses."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=[FlowCellFilter.FILTER_WITH_STATUSES],
        ).all()

    def get_flow_cell_by_name_pattern_and_status(
        self, flow_cell_statuses: list[str], name_pattern: str
    ) -> list[Flowcell]:
        """Return flow cell by name pattern and status."""
        filter_functions: list[FlowCellFilter] = [
            FlowCellFilter.FILTER_WITH_STATUSES,
            FlowCellFilter.FILTER_BY_NAME_SEARCH,
        ]
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            name_search=name_pattern,
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=filter_functions,
        ).all()

    def get_flow_cells_by_case(self, case: Case) -> list[Flowcell] | None:
        """Return flow cells for a case."""
        return apply_flow_cell_filter(
            flow_cells=self._get_join_flow_cell_sample_links_query(),
            filter_functions=[FlowCellFilter.FILTER_BY_CASE],
            case=case,
        ).all()

    def get_samples_from_flow_cell(self, flow_cell_id: str) -> list[Sample] | None:
        """Return samples present on flow cell."""
        flow_cell: Flowcell = self.get_flow_cell_by_name(flow_cell_name=flow_cell_id)
        if flow_cell:
            return flow_cell.samples

    def are_all_flow_cells_on_disk(self, case_id: str) -> bool:
        """Check if flow cells are on disk for sample before starting the analysis."""
        flow_cells: list[Flowcell] | None = self.get_flow_cells_by_case(
            case=self.get_case_by_internal_id(internal_id=case_id)
        )
        if not flow_cells:
            LOG.info("No flow cells found")
            return False
        return all(flow_cell.status == FlowCellStatus.ON_DISK for flow_cell in flow_cells)

    def request_flow_cells_for_case(self, case_id) -> None:
        """Set the status of removed flow cells to REQUESTED for the given case."""
        flow_cells: list[Flowcell] | None = self.get_flow_cells_by_case(
            case=self.get_case_by_internal_id(internal_id=case_id)
        )
        for flow_cell in flow_cells:
            if flow_cell.status == FlowCellStatus.REMOVED:
                flow_cell.status = FlowCellStatus.REQUESTED
                LOG.info(f"Setting status for {flow_cell.name} to {FlowCellStatus.REQUESTED}")
        self.session.commit()

    def get_invoices_by_status(self, is_invoiced: bool = None) -> list[Invoice]:
        """Return invoices by invoiced status."""
        invoices: Query = self._get_query(table=Invoice)
        if is_invoiced:
            return apply_invoice_filter(
                invoices=invoices, filter_functions=[InvoiceFilter.FILTER_BY_INVOICED]
            ).all()
        else:
            return apply_invoice_filter(
                invoices=invoices, filter_functions=[InvoiceFilter.FILTER_BY_NOT_INVOICED]
            ).all()

    def get_invoice_by_entry_id(self, entry_id: int) -> Invoice:
        """Return an invoice."""
        invoices: Query = self._get_query(table=Invoice)
        return apply_invoice_filter(
            invoices=invoices,
            entry_id=entry_id,
            filter_functions=[InvoiceFilter.FILTER_BY_INVOICE_ID],
        ).first()

    def get_pools_and_samples_for_invoice_by_invoice_id(
        self, *, invoice_id: int = None
    ) -> list[Pool | Sample]:
        """Return all pools and samples for an invoice."""
        pools: list[Pool] = apply_pool_filter(
            pools=self._get_query(table=Pool),
            invoice_id=invoice_id,
            filter_functions=[PoolFilter.FILTER_BY_INVOICE_ID],
        ).all()
        samples: list[Sample] = apply_sample_filter(
            samples=self._get_query(table=Sample),
            invoice_id=invoice_id,
            filter_functions=[SampleFilter.FILTER_BY_INVOICE_ID],
        ).all()
        return pools + samples

    def get_case_sample_link(self, case_internal_id: str, sample_internal_id: str) -> CaseSample:
        """Return a case-sample link between a family and a sample."""
        filter_functions: list[CaseSampleFilter] = [
            CaseSampleFilter.GET_SAMPLES_IN_CASE_BY_INTERNAL_ID,
            CaseSampleFilter.GET_CASES_WITH_SAMPLE_BY_INTERNAL_ID,
        ]
        return apply_case_sample_filter(
            filter_functions=filter_functions,
            case_samples=self._get_join_case_sample_query(),
            case_internal_id=case_internal_id,
            sample_internal_id=sample_internal_id,
        ).first()

    def new_invoice_id(self) -> int:
        """Fetch invoices."""
        query: Query = self._get_query(table=Invoice)
        ids = [inv.id for inv in query]
        return max(ids) + 1 if ids else 0

    def get_pools_by_customer_id(self, *, customers: list[Customer] | None = None) -> list[Pool]:
        """Return all the pools for a customer."""
        customer_ids = [customer.id for customer in customers]
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            customer_ids=customer_ids,
            filter_functions=[PoolFilter.FILTER_BY_CUSTOMER_ID],
        ).all()

    def get_pools_by_name_enquiry(self, *, name_enquiry: str = None) -> list[Pool]:
        """Return all the pools with a name fitting the enquiry."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            name_enquiry=name_enquiry,
            filter_functions=[PoolFilter.FILTER_BY_NAME_ENQUIRY],
        ).all()

    def get_pools(self) -> list[Pool]:
        """Return all the pools."""
        return self._get_query(table=Pool).all()

    def get_pools_by_order_enquiry(self, *, order_enquiry: str = None) -> list[Pool]:
        """Return all the pools with an order fitting the enquiry."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            order_enquiry=order_enquiry,
            filter_functions=[PoolFilter.FILTER_BY_ORDER_ENQUIRY],
        ).all()

    def get_pool_by_entry_id(self, entry_id: int) -> Pool:
        """Return a pool by entry id."""
        pools = self._get_query(table=Pool)
        return apply_pool_filter(
            pools=pools, entry_id=entry_id, filter_functions=[PoolFilter.FILTER_BY_ENTRY_ID]
        ).first()

    def get_pools_to_render(
        self, customers: list[Customer] | None = None, enquiry: str = None
    ) -> list[Pool]:
        pools: list[Pool] = (
            self.get_pools_by_customer_id(customers=customers) if customers else self.get_pools()
        )
        if enquiry:
            pools: list[Pool] = list(
                set(
                    self.get_pools_by_name_enquiry(name_enquiry=enquiry)
                    or set(self.get_pools_by_order_enquiry(order_enquiry=enquiry))
                )
            )
        return pools

    def get_ready_made_library_expected_reads(self, case_id: str) -> int:
        """Return the target reads of a ready made library case."""

        application: Application = self.get_application_by_case(case_id=case_id)

        if application.prep_category != PrepCategory.READY_MADE_LIBRARY.value:
            raise ValueError(
                f"{case_id} is not a ready made library, found prep category: "
                f"{application.prep_category}"
            )
        return application.expected_reads

    def get_samples_by_customer_id_and_pattern(
        self, *, customers: list[Customer] | None = None, pattern: str = None
    ) -> list[Sample]:
        """Get samples by customer and sample internal id  or sample name pattern."""
        samples: Query = self._get_query(table=Sample)
        customer_entry_ids: list[int] = []
        filter_functions: list[SampleFilter] = []
        if customers:
            if not isinstance(customers, list):
                customers = list(customers)
            customer_entry_ids = [customer.id for customer in customers]
            filter_functions.append(SampleFilter.FILTER_BY_CUSTOMER_ENTRY_IDS)
        if pattern:
            filter_functions.extend([SampleFilter.FILTER_BY_INTERNAL_ID_OR_NAME_SEARCH])
        filter_functions.append(SampleFilter.ORDER_BY_CREATED_AT_DESC)
        return apply_sample_filter(
            samples=samples,
            customer_entry_ids=customer_entry_ids,
            search_pattern=pattern,
            filter_functions=filter_functions,
        ).all()

    def _get_samples_by_customer_and_subject_id_query(
        self, customer_internal_id: str, subject_id: str
    ) -> Query:
        """Return query of samples of customer with given subject id."""
        records: Query = apply_customer_filter(
            customers=self._get_join_sample_and_customer_query(),
            customer_internal_id=customer_internal_id,
            filter_functions=[CustomerFilter.FILTER_BY_INTERNAL_ID],
        )
        return apply_sample_filter(
            samples=records,
            subject_id=subject_id,
            filter_functions=[SampleFilter.FILTER_BY_SUBJECT_ID],
        )

    def get_samples_by_customer_and_subject_id(
        self, customer_internal_id: str, subject_id: str
    ) -> list[Sample]:
        """Get samples of customer with given subject id."""
        return self._get_samples_by_customer_and_subject_id_query(
            customer_internal_id=customer_internal_id, subject_id=subject_id
        ).all()

    def get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        self, customer_ids: list[int], subject_id: str, is_tumour: bool
    ) -> list[Sample]:
        """Return a list of samples matching a list of customers with given subject id and is a tumour or not."""
        samples = self._get_query(table=Sample)
        filter_functions = [
            SampleFilter.FILTER_BY_CUSTOMER_ENTRY_IDS,
            SampleFilter.FILTER_BY_SUBJECT_ID,
        ]
        (
            filter_functions.append(SampleFilter.FILTER_IS_TUMOUR)
            if is_tumour
            else filter_functions.append(SampleFilter.FILTER_IS_NOT_TUMOUR)
        )
        return apply_sample_filter(
            samples=samples,
            customer_entry_ids=customer_ids,
            subject_id=subject_id,
            filter_functions=filter_functions,
        ).all()

    def get_samples_by_any_id(self, **identifiers: dict) -> Query:
        """Return a sample query filtered by the given names and values of Sample attributes."""
        samples: Query = self._get_query(table=Sample).order_by(Sample.internal_id.desc())
        for identifier_name, identifier_value in identifiers.items():
            samples: Query = apply_sample_filter(
                filter_functions=[SampleFilter.FILTER_BY_IDENTIFIER_NAME_AND_VALUE],
                samples=samples,
                identifier_name=identifier_name,
                identifier_value=identifier_value,
            )
        return samples

    def get_sample_by_name(self, name: str) -> Sample:
        """Get sample by name."""
        samples = self._get_query(table=Sample)
        return apply_sample_filter(
            samples=samples, filter_functions=[SampleFilter.FILTER_BY_SAMPLE_NAME], name=name
        ).first()

    def get_samples_by_type(self, case_id: str, sample_type: SampleType) -> list[Sample] | None:
        """Get samples given a tissue type."""
        samples: Query = apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_SAMPLES_IN_CASE_BY_INTERNAL_ID],
            case_samples=self._get_join_sample_family_query(),
            case_internal_id=case_id,
        )
        samples: Query = apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_WITH_TYPE],
            samples=samples,
            tissue_type=sample_type,
        )
        return samples.all() if samples else None

    def is_case_down_sampled(self, case_id: str) -> bool:
        """Returns True if all samples in a case are down sampled from another sample."""
        case: Case = self.get_case_by_internal_id(internal_id=case_id)
        return all(sample.from_sample is not None for sample in case.samples)

    def is_case_external(self, case_id: str) -> bool:
        """Returns True if all samples in a case have been sequenced externally."""
        case: Case = self.get_case_by_internal_id(internal_id=case_id)
        return all(sample.application_version.application.is_external for sample in case.samples)

    def get_case_by_internal_id(self, internal_id: str) -> Case | None:
        """Get case by internal id."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.FILTER_BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def verify_case_exists(self, case_internal_id: str) -> None:
        """Passes silently if case exists in Status DB, raises error if no case or case samples."""

        case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
        if not case:
            LOG.error(f"Case {case_internal_id} could not be found in Status DB!")
            raise CgError
        if not case.links:
            LOG.error(f"Case {case_internal_id} has no samples in in Status DB!")
            raise CgError
        LOG.info(f"Case {case_internal_id} exists in Status DB")

    def get_running_cases_in_workflow(self, workflow: Workflow) -> list[Case]:
        """Return all running cases in a pipeline."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.FILTER_WITH_WORKFLOW, CaseFilter.FILTER_IS_RUNNING],
            workflow=workflow,
        ).all()

    def get_not_analysed_cases_by_sample_internal_id(
        self,
        sample_internal_id: str,
    ) -> list[Case]:
        """Get not analysed cases by sample internal id."""

        query: Query = self._get_join_case_and_sample_query()

        not_analysed_cases: Query = apply_case_filter(
            cases=query,
            filter_functions=[
                CaseFilter.FILTER_NOT_ANALYSED,
            ],
        )

        return apply_sample_filter(
            samples=not_analysed_cases,
            filter_functions=[SampleFilter.FILTER_BY_INTERNAL_ID],
            internal_id=sample_internal_id,
        ).all()

    def case_with_name_exists(self, case_name: str) -> bool:
        """Check if a case exists in StatusDB."""
        return bool(self.get_case_by_name(case_name))

    def sample_with_id_exists(self, sample_id: str) -> bool:
        """Check if a sample exists in StatusDB."""
        return bool(self.get_sample_by_internal_id(sample_id))

    def get_application_by_tag(self, tag: str) -> Application:
        """Return an application by tag."""
        return apply_application_filter(
            applications=self._get_query(table=Application),
            filter_functions=[ApplicationFilter.FILTER_BY_TAG],
            tag=tag,
        ).first()

    def get_applications_is_not_archived(self) -> list[Application]:
        """Return applications that are not archived."""
        return (
            apply_application_filter(
                applications=self._get_query(table=Application),
                filter_functions=[ApplicationFilter.FILTER_IS_NOT_ARCHIVED],
            )
            .order_by(Application.prep_category, Application.tag)
            .all()
        )

    def get_applications(self) -> list[Application]:
        """Return all applications."""
        return (
            self._get_query(table=Application)
            .order_by(Application.prep_category, Application.tag)
            .all()
        )

    def get_current_application_version_by_tag(self, tag: str) -> ApplicationVersion | None:
        """Return the current application version for an application tag."""
        application = self.get_application_by_tag(tag=tag)
        if not application:
            return None
        return apply_application_versions_filter(
            filter_functions=[
                ApplicationVersionFilter.FILTER_BY_APPLICATION_ENTRY_ID,
                ApplicationVersionFilter.FILTER_BY_VALID_FROM_BEFORE,
                ApplicationVersionFilter.ORDER_BY_VALID_FROM_DESC,
            ],
            application_versions=self._get_query(table=ApplicationVersion),
            application_entry_id=application.id,
            valid_from=dt.datetime.now(),
        ).first()

    def get_bed_version_by_file_name(self, bed_version_file_name: str) -> BedVersion:
        """Return bed version with file name."""
        return apply_bed_version_filter(
            bed_versions=self._get_query(table=BedVersion),
            bed_version_file_name=bed_version_file_name,
            filter_functions=[BedVersionFilter.FILTER_BY_FILE_NAME],
        ).first()

    def get_bed_version_by_short_name(self, bed_version_short_name: str) -> BedVersion:
        """Return bed version with short name."""
        return apply_bed_version_filter(
            bed_versions=self._get_query(table=BedVersion),
            bed_version_short_name=bed_version_short_name,
            filter_functions=[BedVersionFilter.FILTER_BY_SHORT_NAME],
        ).first()

    def get_bed_by_entry_id(self, bed_entry_id: int) -> Bed:
        """Get panel bed with bed entry id."""
        return apply_bed_filter(
            beds=self._get_query(table=Bed),
            filter_functions=[BedFilter.FILTER_BY_ENTRY_ID],
            bed_entry_id=bed_entry_id,
        ).first()

    def get_bed_by_name(self, bed_name: str) -> Bed:
        """Get panel bed with bed name."""
        return apply_bed_filter(
            beds=self._get_query(table=Bed),
            filter_functions=[BedFilter.FILTER_BY_NAME],
            bed_name=bed_name,
        ).first()

    def get_active_beds(self) -> Query:
        """Get all beds that are not archived."""
        bed_filter_functions: list[BedFilter] = [
            BedFilter.FILTER_NOT_ARCHIVED,
            BedFilter.ORDER_BY_NAME,
        ]
        return apply_bed_filter(
            beds=self._get_query(table=Bed), filter_functions=bed_filter_functions
        )

    def get_customer_by_internal_id(self, customer_internal_id: str) -> Customer:
        """Return customer with customer id."""
        return apply_customer_filter(
            filter_functions=[CustomerFilter.FILTER_BY_INTERNAL_ID],
            customers=self._get_query(table=Customer),
            customer_internal_id=customer_internal_id,
        ).first()

    def get_collaboration_by_internal_id(self, internal_id: str) -> Collaboration:
        """Fetch a customer group by internal id from the store."""
        return apply_collaboration_filter(
            collaborations=self._get_query(table=Collaboration),
            filter_functions=[CollaborationFilter.FILTER_BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def get_organism_by_internal_id(self, internal_id: str) -> Organism:
        """Find an organism by internal id."""
        return apply_organism_filter(
            organisms=self._get_query(table=Organism),
            filter_functions=[OrganismFilter.FILTER_BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def get_all_organisms(self) -> list[Organism]:
        """Return all organisms ordered by organism internal id."""
        return self._get_query(table=Organism).order_by(Organism.internal_id)

    def get_customers(self) -> list[Customer]:
        """Return costumers."""
        return self._get_query(table=Customer).all()

    def get_panel_by_abbreviation(self, abbreviation: str) -> Panel:
        """Return a panel by abbreviation."""
        return apply_panel_filter(
            panels=self._get_query(table=Panel),
            filters=[PanelFilter.FILTER_BY_ABBREVIATION],
            abbreviation=abbreviation,
        ).first()

    def get_panels(self) -> list[Panel]:
        """Returns all panels."""
        return self._get_query(table=Panel).order_by(Panel.abbrev).all()

    def get_user_by_email(self, email: str) -> User:
        """Return a user by email from the database."""
        return apply_user_filter(
            users=self._get_query(table=User),
            email=email,
            filter_functions=[UserFilter.FILTER_BY_EMAIL],
        ).first()

    def get_samples_to_receive(self, external: bool = False) -> list[Sample]:
        """Return samples to receive."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_IS_NOT_RECEIVED,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        if external:
            records: Query = apply_application_filter(
                applications=records, filter_functions=[ApplicationFilter.FILTER_IS_EXTERNAL]
            )
        else:
            records: Query = apply_application_filter(
                applications=records,
                filter_functions=[ApplicationFilter.FILTER_IS_NOT_EXTERNAL],
            )
        return records.order_by(Sample.ordered_at).all()

    def get_samples_to_prepare(self) -> list[Sample]:
        """Return samples to prepare."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_IS_RECEIVED,
            SampleFilter.FILTER_IS_NOT_PREPARED,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
            SampleFilter.FILTER_IS_NOT_SEQUENCED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        records: Query = apply_application_filter(
            applications=records, filter_functions=[ApplicationFilter.FILTER_IS_NOT_EXTERNAL]
        )

        return records.order_by(Sample.received_at).all()

    def get_samples_to_sequence(self) -> list[Sample]:
        """Return samples in sequencing."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_IS_PREPARED,
            SampleFilter.FILTER_IS_NOT_SEQUENCED,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        records: Query = apply_application_filter(
            applications=records, filter_functions=[ApplicationFilter.FILTER_IS_NOT_EXTERNAL]
        )
        return records.order_by(Sample.prepared_at).all()

    def get_families_with_analyses(self) -> Query:
        """Return all cases in the database with an analysis."""
        return self._get_outer_join_cases_with_analyses_query()

    def get_families_with_samples(self) -> Query:
        """Return all cases in the database with samples."""
        return self._get_join_cases_with_samples_query()

    def cases_to_analyze(
        self, workflow: Workflow = None, threshold: bool = False, limit: int = None
    ) -> list[Case]:
        """Returns a list if cases ready to be analyzed or set to be reanalyzed."""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.FILTER_HAS_SEQUENCE,
            CaseFilter.FILTER_WITH_WORKFLOW,
            CaseFilter.FILTER_FOR_ANALYSIS,
        ]
        cases = apply_case_filter(
            cases=self.get_families_with_analyses(),
            filter_functions=case_filter_functions,
            workflow=workflow,
        )

        families: list[Query] = list(cases.order_by(Case.ordered_at))
        families = [
            case_obj
            for case_obj in families
            if case_obj.latest_sequenced
            and (
                case_obj.action == CaseActions.ANALYZE
                or not case_obj.latest_analyzed
                or case_obj.latest_analyzed < case_obj.latest_sequenced
            )
        ]

        if threshold:
            families = [case_obj for case_obj in families if case_obj.all_samples_pass_qc]
        return families[:limit]

    def cases(
        self,
        internal_id: str = None,
        name: str = None,
        days: int = 0,
        case_action: str | None = None,
        priority: str = None,
        customer_id: str = None,
        exclude_customer_id: str = None,
        data_analysis: str = None,
        sample_id: str = None,
        only_received: bool = False,
        only_prepared: bool = False,
        only_sequenced: bool = False,
        only_analysed: bool = False,
        only_uploaded: bool = False,
        only_delivered: bool = False,
        only_delivery_reported: bool = False,
        only_invoiced: bool = False,
        exclude_received: bool = False,
        exclude_prepared: bool = False,
        exclude_sequenced: bool = False,
        exclude_analysed: bool = False,
        exclude_uploaded: bool = False,
        exclude_delivered: bool = False,
        exclude_delivery_reported: bool = False,
        exclude_invoiced: bool = False,
    ) -> list[Case]:
        """Fetch cases with and w/o analyses."""
        case_q = self._get_filtered_case_query(
            case_action,
            customer_id,
            data_analysis,
            days,
            exclude_customer_id,
            internal_id,
            name,
            priority,
            sample_id,
        )

        cases = []

        for case_obj in case_q:
            case_data = self._calculate_case_data(case_obj)

            skip_case = self._should_be_skipped(
                case_data,
                exclude_analysed,
                exclude_delivered,
                exclude_delivery_reported,
                exclude_invoiced,
                exclude_prepared,
                exclude_received,
                exclude_sequenced,
                exclude_uploaded,
                only_analysed,
                only_delivered,
                only_delivery_reported,
                only_invoiced,
                only_prepared,
                only_received,
                only_sequenced,
                only_uploaded,
            )

            if skip_case:
                continue

            case_output = self._get_case_output(case_data)

            cases.append(case_output)

        return sorted(cases, key=lambda k: k["tat"], reverse=True)

    def set_case_action(
        self, action: Literal[CaseActions.actions()], case_internal_id: str
    ) -> None:
        """Sets the action of provided cases to None or the given action."""
        case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
        case.action = action
        self.session.commit()

    def get_cases_to_compress(self, date_threshold: datetime) -> list[Case]:
        """Return all cases that are ready to be compressed by SPRING."""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.FILTER_HAS_INACTIVE_ANALYSIS,
            CaseFilter.FILTER_OLD_BY_CREATION_DATE,
            CaseFilter.FILTER_IS_COMPRESSIBLE,
        ]
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=case_filter_functions,
            creation_date=date_threshold,
        ).all()

    def get_sample_by_entry_id(self, entry_id: int) -> Sample:
        """Return a sample by entry id."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_BY_ENTRY_ID],
            samples=self._get_query(table=Sample),
            entry_id=entry_id,
        ).first()

    def get_sample_by_internal_id(self, internal_id: str) -> Sample | None:
        """Return a sample by lims id."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_BY_INTERNAL_ID],
            samples=self._get_query(table=Sample),
            internal_id=internal_id,
        ).first()

    def get_samples_by_internal_id(self, internal_id: str) -> list[Sample]:
        """Return all samples by lims id."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_BY_INTERNAL_ID],
            samples=self._get_query(table=Sample),
            internal_id=internal_id,
        ).all()

    @staticmethod
    def _get_case_output(case_data: SimpleNamespace) -> dict:
        return {
            "data_analysis": case_data.data_analysis,
            "internal_id": case_data.internal_id,
            "name": case_data.name,
            "ordered_at": case_data.ordered_at,
            "total_samples": case_data.total_samples,
            "total_external_samples": case_data.total_external_samples,
            "total_internal_samples": case_data.total_internal_samples,
            "case_external_bool": case_data.case_external_bool,
            "samples_to_receive": case_data.samples_to_receive,
            "samples_to_prepare": case_data.samples_to_prepare,
            "samples_to_sequence": case_data.samples_to_sequence,
            "samples_to_deliver": case_data.samples_to_deliver,
            "samples_to_invoice": case_data.samples_to_invoice,
            "samples_received": case_data.samples_received,
            "samples_prepared": case_data.samples_prepared,
            "samples_sequenced": case_data.samples_sequenced,
            "samples_received_at": case_data.samples_received_at,
            "samples_prepared_at": case_data.samples_prepared_at,
            "samples_sequenced_at": case_data.samples_sequenced_at,
            "samples_delivered_at": case_data.samples_delivered_at,
            "samples_invoiced_at": case_data.samples_invoiced_at,
            "case_action": case_data.case_action,
            "analysis_completed_at": case_data.analysis_completed_at,
            "analysis_uploaded_at": case_data.analysis_uploaded_at,
            "samples_delivered": case_data.samples_delivered,
            "analysis_delivery_reported_at": case_data.analysis_delivery_reported_at,
            "samples_invoiced": case_data.samples_invoiced,
            "analysis_pipeline": case_data.analysis_pipeline,
            "samples_received_bool": case_data.samples_received_bool,
            "samples_prepared_bool": case_data.samples_prepared_bool,
            "samples_sequenced_bool": case_data.samples_sequenced_bool,
            "analysis_completed_bool": case_data.analysis_completed_bool,
            "analysis_uploaded_bool": case_data.analysis_uploaded_bool,
            "samples_delivered_bool": case_data.samples_delivered_bool,
            "analysis_delivery_reported_bool": case_data.analysis_delivery_reported_bool,
            "samples_invoiced_bool": case_data.samples_invoiced_bool,
            "flowcells_status": case_data.flowcells_status,
            "flowcells_on_disk": case_data.flowcells_on_disk,
            "flowcells_on_disk_bool": case_data.flowcells_on_disk_bool,
            "tat": case_data.tat,
            "is_rerun": case_data.is_rerun,
            "max_tat": case_data.max_tat,
        }

    @staticmethod
    def _should_be_skipped(
        case_data: SimpleNamespace,
        exclude_analysed: bool,
        exclude_delivered: bool,
        exclude_delivery_reported: bool,
        exclude_invoiced: bool,
        exclude_prepared: bool,
        exclude_received: bool,
        exclude_sequenced: bool,
        exclude_uploaded: bool,
        only_analysed: bool,
        only_delivered: bool,
        only_delivery_reported: bool,
        only_invoiced: bool,
        only_prepared: bool,
        only_received: bool,
        only_sequenced: bool,
        only_uploaded: bool,
    ) -> bool:
        skip_case = False
        if only_received and not case_data.samples_received_bool:
            skip_case = True
        if only_prepared and not case_data.samples_prepared_bool:
            skip_case = True
        if only_sequenced and not case_data.samples_sequenced_bool:
            skip_case = True
        if only_analysed and not case_data.analysis_completed_bool:
            skip_case = True
        if only_uploaded and not case_data.analysis_uploaded_bool:
            skip_case = True
        if only_delivered and not case_data.samples_delivered_bool:
            skip_case = True
        if only_delivery_reported and not case_data.analysis_delivery_reported_bool:
            skip_case = True
        if only_invoiced and not case_data.samples_invoiced_bool:
            skip_case = True
        if exclude_received and case_data.samples_received_bool:
            skip_case = True
        if exclude_prepared and case_data.samples_prepared_bool:
            skip_case = True
        if exclude_sequenced and case_data.samples_sequenced_bool:
            skip_case = True
        if exclude_analysed and case_data.analysis_completed_bool:
            skip_case = True
        if exclude_uploaded and case_data.analysis_uploaded_bool:
            skip_case = True
        if exclude_delivered and case_data.samples_delivered_bool:
            skip_case = True
        if exclude_delivery_reported and case_data.analysis_delivery_reported_bool:
            skip_case = True
        if exclude_invoiced and case_data.samples_invoiced_bool:
            skip_case = True
        return skip_case

    def _calculate_case_data(self, case_obj: Case) -> SimpleNamespace:
        case_data = self._get_empty_case_data()

        case_data.data_analysis = case_obj.data_analysis
        case_data.internal_id = case_obj.internal_id
        case_data.name = case_obj.name
        case_data.ordered_at = case_obj.ordered_at

        case_data.analysis_in_progress = case_obj.action == "analyze"
        case_data.case_action = case_obj.action
        case_data.total_samples = len(case_obj.links)
        case_data.total_external_samples = len(
            [
                link.sample.application_version.application.is_external
                for link in case_obj.links
                if link.sample.application_version.application.is_external
            ]
        )
        case_data.total_internal_samples = (
            case_data.total_samples - case_data.total_external_samples
        )
        case_data.case_external_bool = case_data.total_external_samples == case_data.total_samples
        if case_data.total_samples > 0:
            case_data.samples_received = len(
                [link.sample.received_at for link in case_obj.links if link.sample.received_at]
            )
            case_data.samples_prepared = len(
                [link.sample.prepared_at for link in case_obj.links if link.sample.prepared_at]
            )
            case_data.samples_sequenced = len(
                [
                    link.sample.last_sequenced_at
                    for link in case_obj.links
                    if link.sample.last_sequenced_at
                ]
            )
            case_data.samples_delivered = len(
                [link.sample.delivered_at for link in case_obj.links if link.sample.delivered_at]
            )
            case_data.samples_invoiced = len(
                [
                    link.sample.invoice.invoiced_at
                    for link in case_obj.links
                    if link.sample.invoice and link.sample.invoice.invoiced_at
                ]
            )

            case_data.samples_to_receive = case_data.total_internal_samples
            case_data.samples_to_prepare = case_data.total_internal_samples
            case_data.samples_to_sequence = case_data.total_internal_samples
            case_data.samples_to_deliver = case_data.total_internal_samples
            case_data.samples_to_invoice = case_data.total_samples - len(
                [link.sample.no_invoice for link in case_obj.links if link.sample.no_invoice]
            )

            case_data.samples_received_bool = (
                case_data.samples_received == case_data.samples_to_receive
            )
            case_data.samples_prepared_bool = (
                case_data.samples_prepared == case_data.samples_to_prepare
            )
            case_data.samples_sequenced_bool = (
                case_data.samples_sequenced == case_data.samples_to_sequence
            )
            case_data.samples_delivered_bool = (
                case_data.samples_delivered == case_data.samples_to_deliver
            )
            case_data.samples_invoiced_bool = (
                case_data.samples_invoiced == case_data.samples_to_invoice
            )

            if case_data.samples_to_receive > 0 and case_data.samples_received_bool:
                case_data.samples_received_at = max(
                    link.sample.received_at
                    for link in case_obj.links
                    if link.sample.received_at is not None
                )

            if case_data.samples_to_prepare > 0 and case_data.samples_prepared_bool:
                case_data.samples_prepared_at = max(
                    link.sample.prepared_at
                    for link in case_obj.links
                    if link.sample.prepared_at is not None
                )

            if case_data.samples_to_sequence > 0 and case_data.samples_sequenced_bool:
                case_data.samples_sequenced_at = max(
                    link.sample.last_sequenced_at
                    for link in case_obj.links
                    if link.sample.last_sequenced_at is not None
                )

            if case_data.samples_to_deliver > 0 and case_data.samples_delivered_bool:
                case_data.samples_delivered_at = max(
                    link.sample.delivered_at
                    for link in case_obj.links
                    if link.sample.delivered_at is not None
                )

            if case_data.samples_to_invoice > 0 and case_data.samples_invoiced_bool:
                case_data.samples_invoiced_at = max(
                    link.sample.invoice.invoiced_at
                    for link in case_obj.links
                    if link.sample.invoice and link.sample.invoice.invoiced_at
                )

            case_data.flowcells = len(list(self.get_flow_cells_by_case(case=case_obj)))
            case_data.flowcells_status = [
                flow_cell.status for flow_cell in self.get_flow_cells_by_case(case=case_obj)
            ]
            case_data.flowcells_on_disk = len(
                [
                    status
                    for status in case_data.flowcells_status
                    if status == FlowCellStatus.ON_DISK
                ]
            )

            if case_data.flowcells < case_data.total_samples:
                case_data.flowcells_status.append("new")

            case_data.flowcells_status = ", ".join(case_data.flowcells_status)

            case_data.flowcells_on_disk_bool = (
                case_data.flowcells_on_disk == case_data.total_samples
            )
        if case_obj.analyses and not case_data.analysis_in_progress:
            case_data.analysis_completed_at = case_obj.analyses[0].completed_at
            case_data.analysis_uploaded_at = case_obj.analyses[0].uploaded_at
            case_data.analysis_delivery_reported_at = case_obj.analyses[
                0
            ].delivery_report_created_at
            case_data.analysis_pipeline = case_obj.analyses[0].pipeline
            case_data.analysis_completed_bool = case_data.analysis_completed_at is not None
            case_data.analysis_uploaded_bool = case_data.analysis_uploaded_at is not None
            case_data.analysis_delivery_reported_bool = (
                case_data.analysis_delivery_reported_at is not None
            )
        elif case_data.total_samples > 0:
            case_data.analysis_completed_bool = False
            case_data.analysis_uploaded_bool = False
            case_data.analysis_delivery_reported_bool = False

        case_data.is_rerun = self._is_rerun(
            case_obj,
            case_data.samples_received_at,
            case_data.samples_prepared_at,
            case_data.samples_sequenced_at,
        )
        case_data.tat = self._calculate_estimated_turnaround_time(
            case_data.is_rerun,
            case_data.case_external_bool,
            case_obj.ordered_at,
            case_data.samples_received_at,
            case_data.samples_prepared_at,
            case_data.samples_sequenced_at,
            case_data.analysis_completed_at,
            case_data.analysis_uploaded_at,
            case_data.samples_delivered_at,
        )
        case_data.max_tat = self._get_max_tat(links=case_obj.links)
        return case_data

    @staticmethod
    def _is_rerun(
        case_obj: Case,
        samples_received_at: datetime,
        samples_prepared_at: datetime,
        samples_sequenced_at: datetime,
    ) -> bool:
        return (
            (len(case_obj.analyses) > 0)
            or (samples_received_at and samples_received_at < case_obj.ordered_at)
            or (samples_prepared_at and samples_prepared_at < case_obj.ordered_at)
            or (samples_sequenced_at and samples_sequenced_at < case_obj.ordered_at)
        )

    def get_analyses_to_upload(self, workflow: Workflow = None) -> list[Analysis]:
        """Return analyses that have not been uploaded."""
        analysis_filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_WITH_WORKFLOW,
            AnalysisFilter.FILTER_COMPLETED,
            AnalysisFilter.FILTER_IS_NOT_UPLOADED,
            AnalysisFilter.FILTER_VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions,
            analyses=self._get_join_analysis_case_query(),
            workflow=workflow,
        ).all()

    def get_analyses_to_clean(
        self, before: datetime = datetime.now(), workflow: Workflow = None
    ) -> list[Analysis]:
        """Return analyses that haven't been cleaned."""
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_IS_UPLOADED,
            AnalysisFilter.FILTER_IS_NOT_CLEANED,
            AnalysisFilter.FILTER_STARTED_AT_BEFORE,
            AnalysisFilter.FILTER_CASE_ACTION_IS_NONE,
        ]
        if workflow:
            filter_functions.append(AnalysisFilter.FILTER_WITH_WORKFLOW)
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_latest_analyses_for_cases_query(),
            workflow=workflow,
            started_at_date=before,
        ).all()

    def get_analyses_for_case_and_workflow_started_at_before(
        self,
        workflow: Workflow,
        started_at_before: datetime,
        case_internal_id: str,
    ) -> list[Analysis]:
        """Return all analyses older than certain date."""
        case = self.get_case_by_internal_id(internal_id=case_internal_id)
        case_entry_id: int = case.id if case else None
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_BY_CASE_ENTRY_ID,
            AnalysisFilter.FILTER_WITH_WORKFLOW,
            AnalysisFilter.FILTER_STARTED_AT_BEFORE,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_query(table=Analysis),
            workflow=workflow,
            case_entry_id=case_entry_id,
            started_at_date=started_at_before,
        ).all()

    def get_analyses_for_case_started_at_before(
        self,
        case_internal_id: str,
        started_at_before: datetime,
    ) -> list[Analysis]:
        """Return all analyses for a case older than certain date."""
        case = self.get_case_by_internal_id(internal_id=case_internal_id)
        case_entry_id: int = case.id if case else None
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_BY_CASE_ENTRY_ID,
            AnalysisFilter.FILTER_STARTED_AT_BEFORE,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_query(table=Analysis),
            case_entry_id=case_entry_id,
            started_at_date=started_at_before,
        ).all()

    def get_analyses_for_workflow_started_at_before(
        self, workflow: Workflow, started_at_before: datetime
    ) -> list[Analysis]:
        """Return all analyses for a pipeline started before a certain date."""
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_WITH_WORKFLOW,
            AnalysisFilter.FILTER_STARTED_AT_BEFORE,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_query(table=Analysis),
            workflow=workflow,
            started_at_date=started_at_before,
        ).all()

    def get_analyses_started_at_before(self, started_at_before: datetime) -> list[Analysis]:
        """Return all analyses for a pipeline started before a certain date."""
        return apply_analysis_filter(
            filter_functions=[AnalysisFilter.FILTER_STARTED_AT_BEFORE],
            analyses=self._get_query(table=Analysis),
            started_at_date=started_at_before,
        ).all()

    def observations_to_upload(self, workflow: Workflow = None) -> Query:
        """Return observations that have not been uploaded."""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.FILTER_WITH_LOQUSDB_SUPPORTED_WORKFLOW,
            CaseFilter.FILTER_WITH_LOQUSDB_SUPPORTED_SEQUENCING_METHOD,
        ]
        records: Query = apply_case_filter(
            cases=self.get_families_with_samples(),
            filter_functions=case_filter_functions,
            workflow=workflow,
        )
        return apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_WITHOUT_LOQUSDB_ID], samples=records
        )

    def observations_uploaded(self, workflow: Workflow = None) -> Query:
        """Return observations that have been uploaded."""
        records: Query = apply_case_filter(
            cases=self.get_families_with_samples(),
            filter_functions=[CaseFilter.FILTER_WITH_LOQUSDB_SUPPORTED_WORKFLOW],
            workflow=workflow,
        )
        records: Query = apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_WITH_LOQUSDB_ID], samples=records
        )
        return records

    def get_analyses(self) -> list[Analysis]:
        return self._get_query(table=Analysis).all()

    def get_analyses_to_deliver_for_pipeline(self, workflow: Workflow = None) -> list[Analysis]:
        """Return analyses that have been uploaded but not delivered."""
        analyses: Query = apply_sample_filter(
            samples=self._get_join_analysis_sample_family_query(),
            filter_functions=[SampleFilter.FILTER_IS_NOT_DELIVERED],
        )
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_IS_NOT_UPLOADED,
            AnalysisFilter.FILTER_WITH_WORKFLOW,
            AnalysisFilter.ORDER_BY_UPLOADED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions, analyses=analyses, workflow=workflow
        ).all()

    def analyses_to_delivery_report(self, workflow: Workflow | None = None) -> Query:
        """Return analyses that need a delivery report to be regenerated."""
        records: Query = apply_case_filter(
            cases=self._get_join_analysis_case_query(),
            filter_functions=[CaseFilter.FILTER_REPORT_SUPPORTED],
        )
        analysis_filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_REPORT_BY_WORKFLOW,
            AnalysisFilter.FILTER_WITHOUT_DELIVERY_REPORT,
            AnalysisFilter.FILTER_VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions, analyses=records, workflow=workflow
        )

    def analyses_to_upload_delivery_reports(self, workflow: Workflow = None) -> Query:
        """Return analyses that need a delivery report to be uploaded."""
        records: Query = apply_case_filter(
            cases=self._get_join_analysis_case_query(),
            filter_functions=[CaseFilter.FILTER_WITH_SCOUT_DELIVERY],
        )
        analysis_filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_REPORT_BY_WORKFLOW,
            AnalysisFilter.FILTER_WITH_DELIVERY_REPORT,
            AnalysisFilter.FILTER_IS_NOT_UPLOADED,
            AnalysisFilter.FILTER_VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions, analyses=records, workflow=workflow
        )

    def get_samples_to_deliver(self) -> list[Sample]:
        """Return all samples not delivered."""
        records = self._get_query(table=Sample)
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_IS_SEQUENCED,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
            SampleFilter.FILTER_IS_NOT_DELIVERED,
        ]

        records: Query = apply_sample_filter(
            filter_functions=sample_filter_functions,
            samples=records,
        )

        return records.all()

    def get_samples_not_invoiced(self) -> list[Sample]:
        """Return all samples that have not been invoiced, excluding those that
        have been down sampled."""
        records = self._get_query(table=Sample)
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_HAS_NO_INVOICE_ID,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
        ]

        records: Query = apply_sample_filter(
            filter_functions=sample_filter_functions,
            samples=records,
        )
        return records.all()

    def get_samples_not_down_sampled(self) -> list[Sample]:
        """Return all samples that have not been down sampled."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED],
            samples=self._get_query(table=Sample),
        ).all()

    def get_samples_to_invoice_query(self) -> Query:
        """Return all samples that should be invoiced."""
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.FILTER_IS_DELIVERED,
            SampleFilter.FILTER_HAS_NO_INVOICE_ID,
            SampleFilter.FILTER_DO_INVOICE,
            SampleFilter.FILTER_IS_NOT_DOWN_SAMPLED,
        ]
        return apply_sample_filter(
            filter_functions=sample_filter_functions,
            samples=self._get_query(table=Sample),
        )

    def get_pools_to_invoice_query(self) -> Query:
        """Return all pools that should be invoiced."""
        pool_filter_functions: list[PoolFilter] = [
            PoolFilter.FILTER_IS_DELIVERED,
            PoolFilter.FILTER_WITHOUT_INVOICE_ID,
            PoolFilter.FILTER_DO_INVOICE,
        ]
        return apply_pool_filter(
            filter_functions=pool_filter_functions,
            pools=self._get_query(table=Pool),
        )

    def get_samples_to_invoice_for_customer(self, customer: Customer = None) -> list[Sample]:
        """Return all samples that should be invoiced for a customer."""
        return apply_sample_filter(
            samples=self.get_samples_to_invoice_query(),
            filter_functions=[SampleFilter.FILTER_BY_CUSTOMER],
            customer=customer,
        ).all()

    def get_pools_to_invoice_for_customer(self, customer: Customer = None) -> list[Pool]:
        """Return all pools for a customer that should be invoiced."""
        return apply_pool_filter(
            filter_functions=[PoolFilter.FILTER_BY_CUSTOMER],
            pools=self.get_pools_to_invoice_query(),
            customer=customer,
        ).all()

    def get_customers_to_invoice(self, records: Query) -> list[Customer]:
        customers_to_invoice: list[Customer] = [
            record.customer
            for record in records.all()
            if record.customer.internal_id != CustomerId.CG_INTERNAL_CUSTOMER
        ]
        return list(set(customers_to_invoice))

    def get_pools_to_receive(self) -> list[Pool]:
        """Return all pools that have been not yet been received."""
        return apply_pool_filter(
            filter_functions=[PoolFilter.FILTER_IS_NOT_RECEIVED], pools=self._get_query(table=Pool)
        ).all()

    def get_all_pools_to_deliver(self) -> list[Pool]:
        """Return all pools that are received but have not yet been delivered."""
        records = self._get_query(table=Pool)
        pool_filter_functions: list[PoolFilter] = [
            PoolFilter.FILTER_IS_RECEIVED,
            PoolFilter.FILTER_IS_NOT_DELIVERED,
        ]

        records: Query = apply_pool_filter(
            filter_functions=pool_filter_functions,
            pools=records,
        )
        return records.all()

    def get_orders_by_workflow(
        self, workflow: str | None = None, limit: int | None = None
    ) -> list[Order]:
        """Returns a list of entries in Order. The output is filtered on workflow and limited, if given."""
        orders: Query = self._get_query(table=Order)
        order_filter_functions: list[Callable] = [OrderFilter.FILTER_ORDERS_BY_WORKFLOW]
        orders: Query = apply_order_filters(
            orders=orders, filter_functions=order_filter_functions, workflow=workflow
        )
        return orders.limit(limit).all()

    def get_order_by_id(self, order_id: int) -> Order | None:
        """Returns the entry in Order matching the given id."""
        orders: Query = self._get_query(table=Order)
        order_filter_functions: list[Callable] = [OrderFilter.FILTER_ORDERS_BY_ID]
        orders: Query = apply_order_filters(
            orders=orders, filter_functions=order_filter_functions, id=order_id
        )
        return orders.first()

    def _calculate_estimated_turnaround_time(
        self,
        is_rerun,
        external_case_bool,
        analysis_ordered_at,
        samples_received_at,
        samples_prepared_at,
        samples_sequenced_at,
        analysis_completed_at,
        analysis_uploaded_at,
        samples_delivered_at,
    ) -> timedelta:
        """Calculated estimated turnaround-time."""
        if samples_received_at and samples_delivered_at:
            return self._calculate_date_delta(None, samples_received_at, samples_delivered_at)

        o_a = self._calculate_date_delta(5, analysis_ordered_at, analysis_completed_at)
        r_p = self._calculate_date_delta(4, samples_received_at, samples_prepared_at)
        p_s = self._calculate_date_delta(5, samples_prepared_at, samples_sequenced_at)
        s_a = self._calculate_date_delta(4, samples_sequenced_at, analysis_completed_at)
        a_u = self._calculate_date_delta(1, analysis_completed_at, analysis_uploaded_at)
        u_d = self._calculate_date_delta(2, analysis_uploaded_at, samples_delivered_at)

        if is_rerun:
            o_a = self._calculate_date_delta(1, analysis_ordered_at, analysis_completed_at)
            return o_a + a_u

        if external_case_bool:
            if analysis_ordered_at and analysis_uploaded_at:
                return self._calculate_date_delta(None, analysis_ordered_at, analysis_uploaded_at)

            return o_a + a_u

        return r_p + p_s + s_a + a_u + u_d

    @staticmethod
    def _calculate_date_delta(default, first_date, last_date) -> timedelta:
        # calculates date delta between two dates, assumes last_date is today if missing
        delta = default
        if not last_date:
            last_date = datetime.now()
        if first_date:
            delta = (last_date - first_date).days
        return delta

    @staticmethod
    def _get_max_tat(links) -> int:
        max_tat = 0
        for link in links:
            if link.sample.application_version.application.turnaround_time:
                max_tat = max(0, link.sample.application_version.application.turnaround_time)
        return max_tat

    @staticmethod
    def _get_empty_case_data() -> SimpleNamespace:
        case_data = SimpleNamespace()
        case_data.data_analysis = None
        case_data.internal_id = None
        case_data.name = None
        case_data.ordered_at = None
        case_data.total_samples = None
        case_data.total_external_samples = None
        case_data.total_internal_samples = None
        case_data.case_external_bool = None
        case_data.samples_to_receive = None
        case_data.samples_to_prepare = None
        case_data.samples_to_sequence = None
        case_data.samples_to_deliver = None
        case_data.samples_to_invoice = None
        case_data.samples_received = None
        case_data.samples_prepared = None
        case_data.samples_sequenced = None
        case_data.samples_received_at = None
        case_data.samples_prepared_at = None
        case_data.samples_sequenced_at = None
        case_data.samples_delivered_at = None
        case_data.samples_invoiced_at = None
        case_data.case_action = None
        case_data.analysis_completed_at = None
        case_data.analysis_uploaded_at = None
        case_data.samples_delivered = None
        case_data.analysis_delivery_reported_at = None

        case_data.samples_invoiced = None
        case_data.analysis_pipeline = None
        case_data.samples_received_bool = None
        case_data.samples_prepared_bool = None
        case_data.samples_sequenced_bool = None
        case_data.analysis_completed_bool = None
        case_data.analysis_uploaded_bool = None
        case_data.samples_delivered_bool = None
        case_data.analysis_delivery_reported_bool = None
        case_data.samples_invoiced_bool = None
        case_data.flowcells_status = None
        case_data.flowcells_on_disk = None
        case_data.flowcells_on_disk_bool = None
        case_data.tat = None
        case_data.is_rerun = None
        case_data.max_tat = None

        return case_data
