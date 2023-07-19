"""Handler to find business data objects."""
import datetime as dt
import logging
from typing import Callable, List, Optional, Iterator, Union, Dict


from sqlalchemy.orm import Query, Session

from cg.constants import FlowCellStatus, Pipeline
from cg.constants.constants import PrepCategory, SampleType
from cg.constants.indexes import ListIndexes
from cg.exc import CaseNotFoundError, CgError
from cg.store.api.base import BaseHandler
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_metrics_filters import SequencingMetricsFilter, apply_metrics_filter

from cg.store.models import (
    Analysis,
    Application,
    Customer,
    Flowcell,
    Family,
    FamilySample,
    Invoice,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
)

from cg.store.filters.status_invoice_filters import apply_invoice_filter, InvoiceFilter
from cg.store.filters.status_pool_filters import apply_pool_filter, PoolFilter

from cg.store.filters.status_flow_cell_filters import apply_flow_cell_filter, FlowCellFilter
from cg.store.filters.status_case_sample_filters import apply_case_sample_filter, CaseSampleFilter
from cg.store.filters.status_sample_filters import apply_sample_filter, SampleFilter

from cg.store.filters.status_analysis_filters import apply_analysis_filter, AnalysisFilter
from cg.store.filters.status_customer_filters import apply_customer_filter, CustomerFilter


LOG = logging.getLogger(__name__)


class FindBusinessDataHandler(BaseHandler):
    """Contains methods to find business data model instances"""

    def __init__(self, session: Session):
        super().__init__(session=session)

    def get_case_by_entry_id(self, entry_id: str) -> Family:
        """Return a case by entry id."""
        cases_query: Query = self._get_query(table=Family)
        return apply_case_filter(
            cases=cases_query, filter_functions=[CaseFilter.FILTER_BY_ENTRY_ID], entry_id=entry_id
        ).first()

    def has_active_cases_for_sample(self, internal_id: str) -> bool:
        """Check if there are any active cases for a sample"""
        sample = self.get_sample_by_internal_id(internal_id=internal_id)
        active_actions = ["analyze", "running"]

        for family_sample in sample.links:
            case: Family = self.get_case_by_entry_id(entry_id=family_sample.family_id)
            if case.action in active_actions:
                return True

        return False

    def get_application_by_case(self, case_id: str) -> Application:
        """Return the application of a case."""

        return (
            self.get_case_by_internal_id(internal_id=case_id)
            .links[ListIndexes.FIRST.value]
            .sample.application_version.application
        )

    def get_latest_analysis_to_upload_for_pipeline(self, pipeline: str = None) -> List[Analysis]:
        """Return latest not uploaded analysis for each case given a pipeline."""
        filter_functions: List[AnalysisFilter] = [
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
        filter_functions: List[AnalysisFilter] = [
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
    ) -> List[Family]:
        """
        Retrieve a list of cases filtered by a customer and matching names.

        Args:
            customer (Customer): The customer object to filter cases by.
            case_name_search (str): The case name search string to filter cases by.

        Returns:
            List[Family]: A list of filtered cases sorted by creation time.
        """
        filter_functions: List[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID,
            CaseFilter.FILTER_BY_NAME_SEARCH,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        return apply_case_filter(
            cases=self._get_query(table=Family),
            filter_functions=filter_functions,
            customer_entry_id=customer.id,
            name_search=case_name_search,
        ).all()

    def get_cases_by_customers_action_and_case_search(
        self,
        customers: Optional[List[Customer]],
        action: Optional[str],
        case_search: Optional[str],
        limit: Optional[int] = 30,
    ) -> List[Family]:
        """
        Retrieve a list of cases filtered by customers, action, and matching names or internal ids.

        Args:
            customers (Optional[List[Customer]]): A list of customer objects to filter cases by.
            action (Optional[str]): The action string to filter cases by.
            case_search (Optional[str]): The case search string to filter cases by.
            limit (Optional[int], default=30): The maximum number of cases to return.

        Returns:
            List[Family]: A list of filtered cases sorted by creation time and limited by the specified number.
        """
        filter_functions: List[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_IDS,
            CaseFilter.FILTER_BY_ACTION,
            CaseFilter.FILTER_BY_CASE_SEARCH,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        customer_entry_ids: List[int] = (
            [customer.id for customer in customers] if customers else None
        )

        filtered_cases: Query = apply_case_filter(
            cases=self._get_query(table=Family),
            filter_functions=filter_functions,
            customer_entry_ids=customer_entry_ids,
            action=action,
            case_search=case_search,
        )
        return filtered_cases.limit(limit=limit).all()

    def get_cases_by_customer_pipeline_and_case_search(
        self,
        customer: Optional[Customer],
        pipeline: Optional[str],
        case_search: Optional[str],
        limit: Optional[int] = 30,
    ) -> List[Family]:
        """
        Retrieve a list of cases filtered by customer, pipeline, and matching names or internal ids.

        Args:
            customer (Optional[Customer]): A customer object to filter cases by.
            pipeline (Optional[str]): The pipeline string to filter cases by.
            case_search (Optional[str]): The case search string to filter cases by.
            limit (Optional[int], default=30): The maximum number of cases to return.

        Returns:
            List[Family]: A list of filtered cases sorted by creation time and limited by the specified number.
        """
        filter_functions: List[Callable] = [
            CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID,
            CaseFilter.FILTER_BY_CASE_SEARCH,
            CaseFilter.FILTER_WITH_PIPELINE,
            CaseFilter.ORDER_BY_CREATED_AT,
        ]

        customer_entry_id: int = customer.id if customer else None

        filtered_cases: Query = apply_case_filter(
            cases=self._get_query(table=Family),
            filter_functions=filter_functions,
            customer_entry_id=customer_entry_id,
            case_search=case_search,
            pipeline=pipeline,
        )
        return filtered_cases.limit(limit=limit).all()

    def get_cases(self) -> List[Family]:
        """Return all cases."""
        return self._get_query(table=Family).all()

    def get_case_samples_by_case_id(self, case_internal_id: str) -> List[FamilySample]:
        """Return the case-sample links associated with a case."""
        return apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_SAMPLES_IN_CASE_BY_INTERNAL_ID],
            case_internal_id=case_internal_id,
            case_samples=self._get_join_case_sample_query(),
        ).all()

    def filter_cases_with_samples(self, case_ids: List[str]) -> List[str]:
        """Return case id:s associated with samples."""
        cases_with_samples = set()
        for case_id in case_ids:
            case: Family = self.get_case_by_internal_id(internal_id=case_id)
            if case and case.links:
                cases_with_samples.add(case_id)
        return list(cases_with_samples)

    def get_cases_by_ticket_id(self, ticket_id: str) -> List[Family]:
        """Return cases associated with a given ticket id."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket_id,
            cases=self._get_query(table=Family),
        ).all()

    def get_customer_id_from_ticket(self, ticket: str) -> str:
        """Returns the customer related to given ticket"""
        cases: List[Family] = self.get_cases_by_ticket_id(ticket_id=ticket)
        if not cases:
            raise ValueError(f"No case found for ticket {ticket}")
        return cases[0].customer.internal_id

    def get_samples_from_ticket(self, ticket: str) -> List[Sample]:
        """Returns the samples related to given ticket."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_BY_TICKET],
            ticket_id=ticket,
            cases=self._get_join_sample_family_query(),
        ).all()

    def get_latest_ticket_from_case(self, case_id: str) -> str:
        """Returns the ticket from the most recent sample in a case"""
        return self.get_case_by_internal_id(internal_id=case_id).latest_ticket

    def get_latest_flow_cell_on_case(self, family_id: str) -> Flowcell:
        """Fetch the latest sequenced flow cell related to a sample on a case."""
        flow_cells_on_case: List[Flowcell] = self.get_flow_cells_by_case(
            case=self.get_case_by_internal_id(internal_id=family_id)
        )
        flow_cells_on_case.sort(key=lambda flow_cell: flow_cell.sequenced_at)
        return flow_cells_on_case[-1] if flow_cells_on_case else None

    def _is_case_found(self, case: Family, case_id: str) -> None:
        """Raise error if case is false."""
        if not case:
            LOG.error(f"Could not find case {case_id}")
            raise CaseNotFoundError("")

    def get_samples_by_case_id(self, case_id: str) -> List[Sample]:
        """Get samples on a given case id."""

        case: Family = self.get_case_by_internal_id(internal_id=case_id)
        self._is_case_found(case=case, case_id=case_id)
        return case.samples if case else []

    def get_sample_ids_by_case_id(self, case_id: str = None) -> Iterator[str]:
        """Return sample ids from case id."""
        case: Family = self.get_case_by_internal_id(internal_id=case_id)
        self._is_case_found(case=case, case_id=case_id)
        for link in case.links:
            yield link.sample.internal_id

    def get_case_by_name_and_customer(self, customer: Customer, case_name: str) -> Family:
        """Find a case by case name within a customer."""
        return apply_case_filter(
            cases=self._get_query(table=Family),
            filter_functions=[CaseFilter.FILTER_BY_CUSTOMER_ENTRY_ID, CaseFilter.FILTER_BY_NAME],
            customer_entry_id=customer.id,
            name=case_name,
        ).first()

    def get_case_by_name(self, name: str) -> Family:
        """Get a case by name."""
        return apply_case_filter(
            cases=self._get_query(table=Family),
            filter_functions=[CaseFilter.FILTER_BY_NAME],
            name=name,
        ).first()

    def get_sample_by_customer_and_name(
        self, customer_entry_id: List[int], sample_name: str
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
        reads_count: Optional[int] = total_reads_query.scalar()
        return reads_count if reads_count else 0

    def get_sample_lane_sequencing_metrics_by_flow_cell_name(
        self, flow_cell_name: str
    ) -> List[SampleLaneSequencingMetrics]:
        """Return sample lane sequencing metrics for a flow cell."""
        return apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[SequencingMetricsFilter.FILTER_METRICS_BY_FLOW_CELL_NAME],
            flow_cell_name=flow_cell_name,
        ).all()

    def get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        self, flow_cell_name: str, sample_internal_id: str, lane: int
    ) -> SampleLaneSequencingMetrics:
        """Get metrics entry by flow cell name, sample internal id and lane."""
        return apply_metrics_filter(
            metrics=self._get_query(table=SampleLaneSequencingMetrics),
            filter_functions=[
                SequencingMetricsFilter.FILTER_METRICS_FOR_FLOW_CELL_SAMPLE_INTERNAL_ID_AND_LANE
            ],
            flow_cell_name=flow_cell_name,
            sample_internal_id=sample_internal_id,
            lane=lane,
        ).first()

    def get_flow_cell_by_name(self, flow_cell_name: str) -> Flowcell:
        """Return flow cell by flow cell name."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_name=flow_cell_name,
            filter_functions=[FlowCellFilter.GET_BY_NAME],
        ).first()

    def get_flow_cells_by_statuses(self, flow_cell_statuses: List[str]) -> Optional[List[Flowcell]]:
        """Return flow cells with supplied statuses."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=[FlowCellFilter.GET_WITH_STATUSES],
        ).all()

    def get_flow_cell_by_name_pattern_and_status(
        self, flow_cell_statuses: List[str], name_pattern: str
    ) -> List[Flowcell]:
        """Return flow cell by name pattern and status."""
        filter_functions: List[FlowCellFilter] = [
            FlowCellFilter.GET_WITH_STATUSES,
            FlowCellFilter.GET_BY_NAME_SEARCH,
        ]
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            name_search=name_pattern,
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=filter_functions,
        ).all()

    def get_flow_cells_by_case(self, case: Family) -> Optional[List[Flowcell]]:
        """Return flow cells for case."""
        return apply_flow_cell_filter(
            flow_cells=self._get_join_flow_cell_sample_links_query(),
            filter_functions=[FlowCellFilter.GET_BY_CASE],
            case=case,
        ).all()

    def get_samples_from_flow_cell(self, flow_cell_id: str) -> Optional[List[Sample]]:
        """Return samples present on flow cell."""
        flow_cell: Flowcell = self.get_flow_cell_by_name(flow_cell_name=flow_cell_id)
        if flow_cell:
            return flow_cell.samples

    def is_all_flow_cells_on_disk(self, case_id: str) -> bool:
        """Check if flow cells are on disk for sample before starting the analysis.
        Flow cells not on disk will be requested.
        """
        flow_cells: Optional[List[Flowcell]] = self.get_flow_cells_by_case(
            case=self.get_case_by_internal_id(internal_id=case_id)
        )

        if not flow_cells:
            LOG.info("No flow cells found")
            return False
        statuses: List[str] = []
        for flow_cell in flow_cells:
            LOG.info(f"{flow_cell.name}: checking if flow cell is on disk")
            LOG.info(f"{flow_cell.name}: status is {flow_cell.status}")
            statuses += [flow_cell.status] if flow_cell.status else []
            if not flow_cell.status or flow_cell.status == FlowCellStatus.REMOVED:
                LOG.info(f"{flow_cell.name}: flow cell not on disk, requesting")
                flow_cell.status = FlowCellStatus.REQUESTED
            elif flow_cell.status != FlowCellStatus.ON_DISK:
                LOG.warning(f"{flow_cell.name}: {flow_cell.status}")
        self.session.commit()
        return all(status == FlowCellStatus.ON_DISK for status in statuses)

    def get_invoices_by_status(self, is_invoiced: bool = None) -> List[Invoice]:
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
    ) -> List[Union[Pool, Sample]]:
        """Return all pools and samples for an invoice."""
        pools: List[Pool] = apply_pool_filter(
            pools=self._get_query(table=Pool),
            invoice_id=invoice_id,
            filter_functions=[PoolFilter.FILTER_BY_INVOICE_ID],
        ).all()
        samples: List[Sample] = apply_sample_filter(
            samples=self._get_query(table=Sample),
            invoice_id=invoice_id,
            filter_functions=[SampleFilter.FILTER_BY_INVOICE_ID],
        ).all()
        return pools + samples

    def get_case_sample_link(self, case_internal_id: str, sample_internal_id: str) -> FamilySample:
        """Return a case-sample link between a family and a sample."""
        filter_functions: List[CaseSampleFilter] = [
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

    def get_pools_by_customer_id(self, *, customers: Optional[List[Customer]] = None) -> List[Pool]:
        """Return all the pools for a customer."""
        customer_ids = [customer.id for customer in customers]
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            customer_ids=customer_ids,
            filter_functions=[PoolFilter.FILTER_BY_CUSTOMER_ID],
        ).all()

    def get_pools_by_name_enquiry(self, *, name_enquiry: str = None) -> List[Pool]:
        """Return all the pools with a name fitting the enquiry."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            name_enquiry=name_enquiry,
            filter_functions=[PoolFilter.FILTER_BY_NAME_ENQUIRY],
        ).all()

    def get_pools(self) -> List[Pool]:
        """Return all the pools."""
        return self._get_query(table=Pool).all()

    def get_pools_by_order_enquiry(self, *, order_enquiry: str = None) -> List[Pool]:
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
        self, customers: Optional[List[Customer]] = None, enquiry: str = None
    ) -> List[Pool]:
        pools: List[Pool] = (
            self.get_pools_by_customer_id(customers=customers) if customers else self.get_pools()
        )
        if enquiry:
            pools: List[Pool] = list(
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
        self, *, customers: Optional[List[Customer]] = None, pattern: str = None
    ) -> List[Sample]:
        """Get samples by customer and sample internal id  or sample name pattern."""
        samples: Query = self._get_query(table=Sample)
        customer_entry_ids: List[int] = []
        filter_functions: List[SampleFilter] = []
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
    ) -> List[Sample]:
        """Get samples of customer with given subject id."""
        return self._get_samples_by_customer_and_subject_id_query(
            customer_internal_id=customer_internal_id, subject_id=subject_id
        ).all()

    def get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        self, customer_ids: List[int], subject_id: str, is_tumour: bool
    ) -> List[Sample]:
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

    def get_samples_by_any_id(self, **identifiers: Dict) -> Query:
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

    def get_samples_by_type(self, case_id: str, sample_type: SampleType) -> Optional[List[Sample]]:
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
        case: Family = self.get_case_by_internal_id(internal_id=case_id)
        return all(sample.from_sample is not None for sample in case.samples)

    def is_case_external(self, case_id: str) -> bool:
        """Returns True if all samples in a case have been sequenced externally."""
        case: Family = self.get_case_by_internal_id(internal_id=case_id)
        return all(sample.application_version.application.is_external for sample in case.samples)

    def get_case_by_internal_id(self, internal_id: str) -> Family:
        """Get case by internal id."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_BY_INTERNAL_ID],
            cases=self._get_query(table=Family),
            internal_id=internal_id,
        ).first()

    def verify_case_exists(self, case_internal_id: str) -> None:
        """Passes silently if case exists in Status DB, raises error if no case or case samples."""

        case: Family = self.get_case_by_internal_id(internal_id=case_internal_id)
        if not case:
            LOG.error(f"Case {case_internal_id} could not be found in Status DB!")
            raise CgError
        if not case.links:
            LOG.error(f"Case {case_internal_id} has no samples in in Status DB!")
            raise CgError
        LOG.info(f"Case {case_internal_id} exists in Status DB")

    def get_running_cases_in_pipeline(self, pipeline: Pipeline) -> List[Family]:
        """Return all running cases in a pipeline."""
        return apply_case_filter(
            filter_functions=[CaseFilter.FILTER_WITH_PIPELINE, CaseFilter.FILTER_IS_RUNNING],
            cases=self._get_query(table=Family),
            pipeline=pipeline,
        ).all()

    def get_not_analysed_cases_by_sample_internal_id(
        self,
        sample_internal_id: str,
    ) -> List[Family]:
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
