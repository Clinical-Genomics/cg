"""Handler to find business data objects."""
import datetime as dt
import logging
from typing import Callable, Iterator

from sqlalchemy.orm import Query, Session

from cg.constants import FlowCellStatus, Pipeline
from cg.constants.constants import PrepCategory, SampleType
from cg.exc import CaseNotFoundError, CgError
from cg.store.api.base import BaseHandler
from cg.store.filters.status_analysis_filters import (
    AnalysisFilter,
    apply_analysis_filter,
)
from cg.store.filters.status_application_limitations_filters import (
    ApplicationLimitationsFilter,
    apply_application_limitations_filter,
)
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_case_sample_filters import (
    CaseSampleFilter,
    apply_case_sample_filter,
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
from cg.store.filters.status_pool_filters import PoolFilter, apply_pool_filter
from cg.store.filters.status_sample_filters import SampleFilter, apply_sample_filter
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    Case,
    CaseSample,
    Customer,
    Flowcell,
    Invoice,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
)

LOG = logging.getLogger(__name__)


class FindBusinessDataHandler(BaseHandler):
    """Contains methods to find business data model instances."""

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
            application_limitations=self._get_join_application_limitations_query(),
            filter_functions=[ApplicationLimitationsFilter.FILTER_BY_TAG],
            tag=tag,
        ).all()

    def get_application_limitation_by_tag_and_pipeline(
        self, tag: str, pipeline: Pipeline
    ) -> ApplicationLimitations | None:
        """Return an application limitation given the application tag and pipeline."""
        filter_functions: list[ApplicationLimitationsFilter] = [
            ApplicationLimitationsFilter.FILTER_BY_TAG,
            ApplicationLimitationsFilter.FILTER_BY_PIPELINE,
        ]
        return apply_application_limitations_filter(
            application_limitations=self._get_join_application_limitations_query(),
            filter_functions=filter_functions,
            tag=tag,
            pipeline=pipeline,
        ).first()

    def get_latest_analysis_to_upload_for_pipeline(self, pipeline: str = None) -> list[Analysis]:
        """Return latest not uploaded analysis for each case given a pipeline."""
        filter_functions: list[AnalysisFilter] = [
            AnalysisFilter.FILTER_WITH_PIPELINE,
            AnalysisFilter.FILTER_IS_NOT_UPLOADED,
        ]
        return apply_analysis_filter(
            analyses=self._get_latest_analyses_for_cases_query(),
            filter_functions=filter_functions,
            pipeline=pipeline,
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
            analyses=self._get_query(Analysis),
            case_entry_id=case_entry_id,
            started_at_date=started_at_date,
            filter_functions=filter_functions,
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
            customer_entry_ids=customer_entry_ids,
            action=action,
            case_search=case_search,
        )
        return filtered_cases.limit(limit=limit).all()

    def get_cases_by_customer_pipeline_and_case_search(
        self,
        customer: Customer | None,
        pipeline: str | None,
        case_search: str | None,
        limit: int | None = 30,
    ) -> list[Case]:
        """
        Retrieve a list of cases filtered by customer, pipeline, and matching names or internal ids.

        Args:
            customer (Customer | None): A customer object to filter cases by.
            pipeline (str | None): The pipeline string to filter cases by.
            case_search (str | None): The case search string to filter cases by.
            limit (int | None, default=30): The maximum number of cases to return.

        Returns:
            list[Case]: A list of filtered cases sorted by creation time and limited by the specified number.
        """
        filter_functions: list[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID,
            CaseFilter.FILTER_BY_CASE_SEARCH,
            CaseFilter.FILTER_WITH_PIPELINE,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        customer_entry_id: int = customer.id if customer else None

        filtered_cases: Query = apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=filter_functions,
            customer_entry_id=customer_entry_id,
            case_search=case_search,
            pipeline=pipeline,
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
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket_id,
            cases=self._get_query(table=Case),
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
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket,
            cases=self._get_join_sample_family_query(),
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
        sequencing_metrics: list[
            SampleLaneSequencingMetrics
        ] = self.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name=flow_cell_name)
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
        sequencing_metrics: list[
            SampleLaneSequencingMetrics
        ] = self.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name=flow_cell_name)
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
        """Return flow cells for case."""
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
        filter_functions.append(
            SampleFilter.FILTER_IS_TUMOUR
        ) if is_tumour else filter_functions.append(SampleFilter.FILTER_IS_NOT_TUMOUR)
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

    def get_case_by_internal_id(self, internal_id: str) -> Case:
        """Get case by internal id."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_BY_INTERNAL_ID],
            cases=self._get_query(table=Case),
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

    def get_running_cases_in_pipeline(self, pipeline: Pipeline) -> list[Case]:
        """Return all running cases in a pipeline."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_WITH_PIPELINE, CaseFilter.FILTER_IS_RUNNING],
            cases=self._get_query(table=Case),
            pipeline=pipeline,
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
