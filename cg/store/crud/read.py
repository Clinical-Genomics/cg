"""Handler to read data objects."""

import datetime as dt
import logging
from datetime import datetime
from typing import Callable, Iterator

from sqlalchemy.orm import Query

from cg.constants import SequencingRunDataAvailability, Workflow
from cg.constants.constants import (
    DNA_WORKFLOWS_WITH_SCOUT_UPLOAD,
    CaseActions,
    CustomerId,
    SampleType,
)
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import DNA_PREP_CATEGORIES, SeqLibraryPrepCategory
from cg.exc import (
    AnalysisDoesNotExistError,
    AnalysisNotCompletedError,
    CaseNotFoundError,
    CgDataError,
    CgError,
    OrderNotFoundError,
    SampleNotFoundError,
)
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import SexEnum
from cg.server.dto.samples.requests import CollaboratorSamplesRequest
from cg.services.orders.order_service.models import OrderQueryParams
from cg.store.api.data_classes import RNADNACollection
from cg.store.base import BaseHandler
from cg.store.exc import EntryNotFoundError
from cg.store.filters.status_analysis_filters import AnalysisFilter, apply_analysis_filter
from cg.store.filters.status_application_filters import ApplicationFilter, apply_application_filter
from cg.store.filters.status_application_limitations_filters import (
    ApplicationLimitationsFilter,
    apply_application_limitations_filter,
)
from cg.store.filters.status_application_version_filters import (
    ApplicationVersionFilter,
    apply_application_versions_filter,
)
from cg.store.filters.status_bed_filters import BedFilter, apply_bed_filter
from cg.store.filters.status_bed_version_filters import BedVersionFilter, apply_bed_version_filter
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_case_sample_filters import CaseSampleFilter, apply_case_sample_filter
from cg.store.filters.status_collaboration_filters import (
    CollaborationFilter,
    apply_collaboration_filter,
)
from cg.store.filters.status_customer_filters import CustomerFilter, apply_customer_filter
from cg.store.filters.status_illumina_flow_cell_filters import (
    IlluminaFlowCellFilter,
    apply_illumina_flow_cell_filters,
)
from cg.store.filters.status_illumina_metrics_filters import (
    IlluminaMetricsFilter,
    apply_illumina_metrics_filter,
)
from cg.store.filters.status_illumina_sequencing_run_filters import (
    IlluminaSequencingRunFilter,
    apply_illumina_sequencing_run_filter,
)
from cg.store.filters.status_invoice_filters import InvoiceFilter, apply_invoice_filter
from cg.store.filters.status_order_filters import OrderFilter, apply_order_filters
from cg.store.filters.status_ordertype_application_filters import (
    OrderTypeApplicationFilter,
    apply_order_type_application_filter,
)
from cg.store.filters.status_organism_filters import OrganismFilter, apply_organism_filter
from cg.store.filters.status_pacbio_smrt_cell_filters import (
    PacBioSMRTCellFilter,
    apply_pac_bio_smrt_cell_filters,
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
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    InstrumentRun,
    Invoice,
    Order,
    OrderTypeApplication,
    Organism,
    PacbioSampleSequencingMetrics,
    PacbioSequencingRun,
    PacbioSMRTCell,
    Panel,
    Pool,
    RunDevice,
    Sample,
    SampleRunMetrics,
    User,
)

LOG = logging.getLogger(__name__)


class ReadHandler(BaseHandler):
    """Class for reading items in the database."""

    def get_case_by_entry_id(self, entry_id: str) -> Case:
        """Return a case by entry id."""
        cases_query: Query = self._get_query(table=Case)
        return apply_case_filter(
            cases=cases_query, filter_functions=[CaseFilter.BY_ENTRY_ID], entry_id=entry_id
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

    def get_application_limitations_by_tag(self, tag: str) -> list[ApplicationLimitations]:
        """Return application limitations given the application tag."""
        return apply_application_limitations_filter(
            filter_functions=[ApplicationLimitationsFilter.BY_TAG],
            application_limitations=self._get_join_application_limitations_query(),
            tag=tag,
        ).all()

    def get_application_limitation_by_tag_and_workflow(
        self, tag: str, workflow: Workflow
    ) -> ApplicationLimitations | None:
        """Return an application limitation given the application tag and workflow."""
        filter_functions: list[ApplicationLimitationsFilter] = [
            ApplicationLimitationsFilter.BY_TAG,
            ApplicationLimitationsFilter.BY_WORKFLOW,
        ]
        return apply_application_limitations_filter(
            filter_functions=filter_functions,
            application_limitations=self._get_join_application_limitations_query(),
            tag=tag,
            workflow=workflow,
        ).first()

    def get_latest_analysis_to_upload_for_workflow(
        self, workflow: Workflow | None = None
    ) -> list[Analysis]:
        """Return latest not uploaded analysis for each case given a workflow."""
        filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.WITH_WORKFLOW,
            AnalysisFilter.IS_NOT_UPLOADED,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_latest_analyses_for_cases_query(),
            workflow=workflow,
        ).all()

    def get_latest_started_analysis_for_case(self, case_id: str) -> Analysis:
        """Return the latest started analysis for a case.
        Raises:
            AnalysisDoesNotExistError if no analysis is found.
        """
        case: Case | None = self.get_case_by_internal_id(case_id)
        analyses: list[Analysis] = case.analyses
        if not analyses:
            raise AnalysisDoesNotExistError(f"No analysis found for case {case_id}")
        analyses.sort(key=lambda x: x.started_at, reverse=True)
        analysis: Analysis = analyses[0]
        return analysis

    def get_latest_completed_analysis_for_case(self, case_id: str) -> Analysis:
        """Return the latest completed analysis for a case.
        Raises:
            AnalysisDoesNotExistError if no analysis is found.
        """
        case: Case | None = self.get_case_by_internal_id(case_id)
        if not case.analyses:
            raise AnalysisDoesNotExistError(f"No analysis found for case {case_id}")
        completed_analyses: list[Analysis] = [
            analysis for analysis in case.analyses if analysis.completed_at
        ]
        if not completed_analyses:
            raise AnalysisNotCompletedError(f"No completed analysis found for case {case_id}")
        completed_analyses.sort(key=lambda x: x.completed_at, reverse=True)
        return completed_analyses[0]

    def get_analysis_by_entry_id(self, entry_id: int) -> Analysis | None:
        """Return an analysis."""
        return apply_analysis_filter(
            filter_functions=[AnalysisFilter.BY_ENTRY_ID],
            analyses=self._get_query(table=Analysis),
            entry_id=entry_id,
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
            CaseFilter.BY_CUSTOMER_ENTRY_ID,
            CaseFilter.BY_NAME_SEARCH,
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
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Case], int]:
        """
        Return cases by customers, action, and matching names or internal ids, plus the total
        number of cases matching the filter criteria. A limit and offset can be applied to the
        query for pagination purposes.

        Args:
            customers (list[Customer] | None): A list of customer objects to filter cases by.
            action (str | None): The action string to filter cases by.
            case_search (str | None): The case search string to filter cases by.
            limit (int | None, default=50): The maximum number of cases to return.
            offset (int, default=0): The offset number of cases for the query.
        Returns:
            list[Case]: A list of filtered cases sorted by creation time and truncated
                        by the limit parameter.
            int: The total number of cases returned before truncation.
        """
        filter_functions: list[Callable] = [
            CaseFilter.BY_CUSTOMER_ENTRY_IDS,
            CaseFilter.BY_ACTION,
            CaseFilter.BY_CASE_SEARCH,
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
        total: int = filtered_cases.count()
        return filtered_cases.offset(offset).limit(limit=limit).all(), total

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
            CaseFilter.BY_CUSTOMER_ENTRY_ID,
            CaseFilter.BY_CASE_SEARCH,
            CaseFilter.WITH_WORKFLOW,
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
            filter_functions=[CaseSampleFilter.SAMPLES_IN_CASE_BY_INTERNAL_ID],
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
        if order := apply_order_filters(
            orders=self._get_query(table=Order),
            filters=[OrderFilter.BY_TICKET_ID],
            ticket_id=int(ticket_id),
        ).first():
            return order.cases
        return []

    def get_customer_id_from_ticket(self, ticket: str) -> str:
        """Returns the customer related to given ticket."""
        if order := self.get_order_by_ticket_id(int(ticket)):
            return order.customer.internal_id
        raise ValueError(f"No order found for ticket {ticket}")

    def get_samples_from_ticket(self, ticket: str) -> list[Sample]:
        """Returns the samples related to given ticket."""
        return apply_order_filters(
            orders=self._get_join_sample_case_order_query(),
            filters=[OrderFilter.BY_TICKET_ID],
            ticket_id=int(ticket),
        ).all()

    def get_latest_ticket_from_case(self, case_id: str) -> str:
        """Returns the ticket from the most recent sample in a case."""
        return str(self.get_case_by_internal_id(internal_id=case_id).latest_order.ticket_id)

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
            filter_functions=[CaseFilter.BY_CUSTOMER_ENTRY_ID, CaseFilter.BY_NAME],
            customer_entry_id=customer.id,
            name=case_name,
        ).first()

    def get_case_by_name(self, name: str) -> Case:
        """Get a case by name."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.BY_NAME],
            name=name,
        ).first()

    def get_sample_by_customer_and_name(
        self, customer_entry_id: list[int], sample_name: str
    ) -> Sample:
        """Get samples within a customer."""
        filter_functions = [
            SampleFilter.BY_CUSTOMER_ENTRY_IDS,
            SampleFilter.BY_SAMPLE_NAME,
        ]

        return apply_sample_filter(
            samples=self._get_query(table=Sample),
            filter_functions=filter_functions,
            customer_entry_ids=customer_entry_id,
            name=sample_name,
        ).first()

    def get_illumina_metrics_entry_by_device_sample_and_lane(
        self, device_internal_id: str, sample_internal_id: str, lane: int
    ) -> IlluminaSampleSequencingMetrics:
        """Get metrics entry by sequencing device internal id, sample internal id and lane."""
        filtered_metrics: Query = apply_illumina_metrics_filter(
            metrics=self._get_joined_illumina_sample_tables(),
            filter_functions=[IlluminaMetricsFilter.BY_LANE],
            lane=lane,
        )
        filtered_flow_cells: Query = apply_illumina_flow_cell_filters(
            flow_cells=filtered_metrics,
            filter_functions=[IlluminaFlowCellFilter.BY_INTERNAL_ID],
            internal_id=device_internal_id,
        )
        filtered_samples: Query = apply_sample_filter(
            samples=filtered_flow_cells,
            filter_functions=[SampleFilter.BY_INTERNAL_ID],
            internal_id=sample_internal_id,
        )
        return filtered_samples.first()

    def get_illumina_sequencing_run_by_device_internal_id(
        self, device_internal_id: str
    ) -> IlluminaSequencingRun:
        """Get Illumina sequencing run entry by device internal id."""
        sequencing_run: IlluminaSequencingRun | None = apply_illumina_sequencing_run_filter(
            runs=self._get_query(table=IlluminaSequencingRun),
            filter_functions=[IlluminaSequencingRunFilter.BY_DEVICE_INTERNAL_ID],
            device_internal_id=device_internal_id,
        ).first()
        if not sequencing_run:
            raise EntryNotFoundError(f"No sequencing run found for device {device_internal_id}")
        return sequencing_run

    def get_latest_illumina_sequencing_run_for_nipt_case(
        self, case_internal_id: str
    ) -> IlluminaSequencingRun:
        """
        Get Illumina sequencing run entry by case internal id.
        NIPT runs all samples under a single case on the same sequencing run.
        """

        case: Case = self.get_case_by_internal_id(case_internal_id)
        if case.data_analysis != Workflow.FLUFFY:
            raise CgError(f"Case {case_internal_id} is not a NIPT case")
        sequencing_runs: list[IlluminaSequencingRun] = self.get_illumina_sequencing_runs_by_case(
            case.internal_id
        )
        return max(sequencing_runs, key=lambda run: run.sequencing_completed_at)

    def get_illumina_sequencing_runs_by_data_availability(
        self, data_availability: list[str]
    ) -> list[IlluminaSequencingRun] | None:
        """Return Illumina sequencing runs with supplied statuses."""
        return apply_illumina_sequencing_run_filter(
            runs=self._get_query(table=IlluminaSequencingRun),
            data_availability=data_availability,
            filter_functions=[IlluminaSequencingRunFilter.WITH_DATA_AVAILABILITY],
        ).all()

    def get_samples_by_illumina_flow_cell(self, flow_cell_id: str) -> list[Sample] | None:
        """Return samples present on an Illumina flow cell."""
        sequencing_run: IlluminaSequencingRun = (
            self.get_illumina_sequencing_run_by_device_internal_id(device_internal_id=flow_cell_id)
        )
        if sequencing_run:
            return sequencing_run.device.samples

    def get_illumina_sequencing_runs_by_case(
        self, case_id: str
    ) -> list[IlluminaSequencingRun] | None:
        """Get all Illumina sequencing runs for a case."""
        case: Case = self.get_case_by_internal_id(case_id)
        samples_on_case: list[Sample] = case.samples
        sample_metrics: list[SampleRunMetrics] = []
        for sample in samples_on_case:
            sample_metrics.extend(sample.sample_run_metrics)
        sequencing_runs: list[IlluminaSequencingRun] = [
            apply_illumina_sequencing_run_filter(
                runs=self._get_query(IlluminaSequencingRun),
                filter_functions=[IlluminaSequencingRunFilter.BY_ENTRY_ID],
                entry_id=sample_metric.instrument_run_id,
            ).first()
            for sample_metric in sample_metrics
        ]
        return sequencing_runs

    def are_all_illumina_runs_on_disk(self, case_id: str) -> bool:
        """Check if Illumina runs are on disk for sample before starting the analysis."""
        sequencing_runs: list[IlluminaSequencingRun] | None = (
            self.get_illumina_sequencing_runs_by_case(case_id)
        )
        if not sequencing_runs:
            LOG.info("No sequencing runs found")
            return False
        return all(
            sequencing_run.data_availability == SequencingRunDataAvailability.ON_DISK
            for sequencing_run in sequencing_runs
        )

    def request_sequencing_runs_for_case(self, case_id) -> None:
        """Set the status of removed Illumina sequencing runs to REQUESTED for the given case."""
        sequencing_runs: list[IlluminaSequencingRun] | None = (
            self.get_illumina_sequencing_runs_by_case(case_id)
        )
        for sequencing_run in sequencing_runs:
            if sequencing_run.data_availability == SequencingRunDataAvailability.REMOVED:
                sequencing_run.data_availability = SequencingRunDataAvailability.REQUESTED
                LOG.info(
                    f"Setting status for {sequencing_run.device.internal_id} to {SequencingRunDataAvailability.REQUESTED}"
                )
        self.session.commit()

    def get_invoices_by_status(self, is_invoiced: bool = None) -> list[Invoice]:
        """Return invoices by invoiced status."""
        invoices: Query = self._get_query(table=Invoice)
        if is_invoiced:
            return apply_invoice_filter(
                invoices=invoices, filter_functions=[InvoiceFilter.BY_INVOICED]
            ).all()
        else:
            return apply_invoice_filter(
                invoices=invoices, filter_functions=[InvoiceFilter.BY_NOT_INVOICED]
            ).all()

    def get_invoice_by_entry_id(self, entry_id: int) -> Invoice:
        """Return an invoice."""
        invoices: Query = self._get_query(table=Invoice)
        return apply_invoice_filter(
            invoices=invoices,
            entry_id=entry_id,
            filter_functions=[InvoiceFilter.BY_INVOICE_ID],
        ).first()

    def get_pools_and_samples_for_invoice_by_invoice_id(
        self, *, invoice_id: int = None
    ) -> list[Pool | Sample]:
        """Return all pools and samples for an invoice."""
        pools: list[Pool] = apply_pool_filter(
            pools=self._get_query(table=Pool),
            invoice_id=invoice_id,
            filter_functions=[PoolFilter.BY_INVOICE_ID],
        ).all()
        samples: list[Sample] = apply_sample_filter(
            samples=self._get_query(table=Sample),
            invoice_id=invoice_id,
            filter_functions=[SampleFilter.BY_INVOICE_ID],
        ).all()
        return pools + samples

    def get_case_sample_link(self, case_internal_id: str, sample_internal_id: str) -> CaseSample:
        """Return a case-sample link between a family and a sample."""
        filter_functions: list[CaseSampleFilter] = [
            CaseSampleFilter.SAMPLES_IN_CASE_BY_INTERNAL_ID,
            CaseSampleFilter.CASES_WITH_SAMPLE_BY_INTERNAL_ID,
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

    def get_pools_by_customers(self, *, customers: list[Customer] | None = None) -> list[Pool]:
        """Return all the pools for a list of customers."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            customers=customers,
            filter_functions=[PoolFilter.BY_CUSTOMERS],
        ).all()

    def get_pools_by_name_enquiry(self, *, name_enquiry: str = None) -> list[Pool]:
        """Return all the pools with a name fitting the enquiry."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            name_enquiry=name_enquiry,
            filter_functions=[PoolFilter.BY_NAME_ENQUIRY],
        ).all()

    def get_pools(self) -> list[Pool]:
        """Return all the pools."""
        return self._get_query(table=Pool).all()

    def get_pools_by_order_enquiry(self, *, order_enquiry: str = None) -> list[Pool]:
        """Return all the pools with an order fitting the enquiry."""
        return apply_pool_filter(
            pools=self._get_query(table=Pool),
            order_enquiry=order_enquiry,
            filter_functions=[PoolFilter.BY_ORDER_ENQUIRY],
        ).all()

    def get_pool_by_entry_id(self, entry_id: int) -> Pool:
        """Return a pool by entry id."""
        pools = self._get_query(table=Pool)
        return apply_pool_filter(
            pools=pools, entry_id=entry_id, filter_functions=[PoolFilter.BY_ENTRY_ID]
        ).first()

    def get_pools_to_render(
        self, customers: list[Customer] | None = None, enquiry: str = None
    ) -> list[Pool]:
        pools: list[Pool] = (
            self.get_pools_by_customers(customers=customers) if customers else self.get_pools()
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

        if application.prep_category != SeqLibraryPrepCategory.READY_MADE_LIBRARY.value:
            raise ValueError(
                f"{case_id} is not a ready made library, found prep category: "
                f"{application.prep_category}"
            )
        return application.expected_reads

    def get_samples_by_customers_and_pattern(
        self,
        *,
        customers: list[Customer] | None = None,
        pattern: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Sample], int]:
        """
        Return the samples by customer and internal id or name pattern, plus the total number of
        samples matching the filter criteria. A limit and offset can be applied to the query for
        pagination purposes.

        Args:
            customers (list[Customer] | None): A list of customer objects to filter cases by.
            pattern (str | None): The sample internal id or name pattern to search for.
            limit (int | None, default=50): The maximum number of samples to return.
            offset (int, default=0): The offset number of samples for the query.
        Returns:
            list[Sample]: A list of filtered samples truncated by the limit parameter.
            int: The total number of samples returned before truncation.
        """
        samples: Query = self._get_query(table=Sample)
        filter_functions: list[SampleFilter] = []
        if customers:
            if not isinstance(customers, list):
                customers = list(customers)
            filter_functions.append(SampleFilter.BY_CUSTOMERS)
        if pattern:
            filter_functions.extend([SampleFilter.BY_INTERNAL_ID_OR_NAME_SEARCH])
        filter_functions.append(SampleFilter.ORDER_BY_CREATED_AT_DESC)
        samples: Query = apply_sample_filter(
            samples=samples,
            customers=customers,
            search_pattern=pattern,
            filter_functions=filter_functions,
        )
        total: int = samples.count()
        return samples.offset(offset).limit(limit).all(), total

    def get_collaborator_samples(self, request: CollaboratorSamplesRequest) -> list[Sample]:
        customer: Customer | None = self.get_customer_by_internal_id(request.customer)
        collaborator_ids = [collaborator.id for collaborator in customer.collaborators]

        filters = [
            SampleFilter.BY_CUSTOMER_ENTRY_IDS,
            SampleFilter.BY_INTERNAL_ID_OR_NAME_SEARCH,
            SampleFilter.ORDER_BY_CREATED_AT_DESC,
            SampleFilter.IS_NOT_CANCELLED,
        ]
        query = (
            self._get_query(table=Sample)
            .join(Sample.application_version)
            .join(ApplicationVersion.application)
            .join(Application.order_type_applications)
        )
        samples: Query = apply_sample_filter(
            samples=query,
            customer_entry_ids=collaborator_ids,
            search_pattern=request.enquiry,
            filter_functions=filters,
        )
        if request.order_type:
            samples = samples.filter(OrderTypeApplication.order_type == request.order_type)
        return samples.limit(request.limit).all()

    def _get_samples_by_customer_and_subject_id_query(
        self, customer_internal_id: str, subject_id: str
    ) -> Query:
        """Return query of samples of customer with given subject id."""
        records: Query = apply_customer_filter(
            customers=self._get_join_sample_and_customer_query(),
            customer_internal_id=customer_internal_id,
            filter_functions=[CustomerFilter.BY_INTERNAL_ID],
        )
        return apply_sample_filter(
            samples=records,
            subject_id=subject_id,
            filter_functions=[SampleFilter.BY_SUBJECT_ID],
        )

    def get_samples_by_customer_and_subject_id(
        self, customer_internal_id: str, subject_id: str
    ) -> list[Sample]:
        """Get samples of customer with given subject id."""
        return self._get_samples_by_customer_and_subject_id_query(
            customer_internal_id=customer_internal_id, subject_id=subject_id
        ).all()

    def get_samples_by_any_id(self, **identifiers: dict) -> Query:
        """Return a sample query filtered by the given names and values of Sample attributes."""
        samples: Query = self._get_query(table=Sample).order_by(Sample.internal_id.desc())
        for identifier_name, identifier_value in identifiers.items():
            samples: Query = apply_sample_filter(
                filter_functions=[SampleFilter.BY_IDENTIFIER_NAME_AND_VALUE],
                samples=samples,
                identifier_name=identifier_name,
                identifier_value=identifier_value,
            )
        return samples

    def get_sample_by_name(self, name: str) -> Sample:
        """Get sample by name."""
        samples = self._get_query(table=Sample)
        return apply_sample_filter(
            samples=samples, filter_functions=[SampleFilter.BY_SAMPLE_NAME], name=name
        ).first()

    def get_samples_by_type(self, case_id: str, sample_type: SampleType) -> list[Sample] | None:
        """Get samples given a tissue type."""
        samples: Query = apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.SAMPLES_IN_CASE_BY_INTERNAL_ID],
            case_samples=self._get_join_sample_family_query(),
            case_internal_id=case_id,
        )
        samples: Query = apply_sample_filter(
            filter_functions=[SampleFilter.WITH_TYPE],
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
            filter_functions=[CaseFilter.BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def get_cases_by_internal_ids(self, internal_ids: list[str]) -> list[Case]:
        """Get cases by internal ids."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.BY_INTERNAL_IDS],
            internal_ids=internal_ids,
        ).all()

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
        """Return all running cases in a workflow."""
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=[CaseFilter.WITH_WORKFLOW, CaseFilter.IS_RUNNING],
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
                CaseFilter.NOT_ANALYSED,
            ],
        )

        return apply_sample_filter(
            samples=not_analysed_cases,
            filter_functions=[SampleFilter.BY_INTERNAL_ID],
            internal_id=sample_internal_id,
        ).all()

    def case_with_name_exists(self, case_name: str) -> bool:
        """Check if a case exists in StatusDB."""
        return bool(self.get_case_by_name(case_name))

    def sample_with_id_exists(self, sample_id: str) -> bool:
        """Check if a sample exists in StatusDB."""
        return bool(self.get_sample_by_internal_id(sample_id))

    def get_application_by_tag(self, tag: str) -> Application | None:
        """Return an application by tag."""
        return apply_application_filter(
            applications=self._get_query(table=Application),
            filter_functions=[ApplicationFilter.BY_TAG],
            tag=tag,
        ).first()

    def get_applications_is_not_archived(self) -> list[Application]:
        """Return applications that are not archived."""
        return (
            apply_application_filter(
                applications=self._get_query(table=Application),
                filter_functions=[ApplicationFilter.IS_NOT_ARCHIVED],
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

    def get_active_applications_by_order_type(self, order_type: OrderType) -> list[Application]:
        """
        Return all possible non-archived applications with versions for an order type.
        Raises:
            EntryNotFoundError: If no applications are found for the order type.
        """
        filters: list[ApplicationFilter] = [
            ApplicationFilter.IS_NOT_ARCHIVED,
            ApplicationFilter.HAS_VERSIONS,
        ]
        non_archived_applications: Query = apply_application_filter(
            applications=self._get_join_application_ordertype_query(),
            filter_functions=filters,
        )
        applications: list[Application] = apply_order_type_application_filter(
            order_type_applications=non_archived_applications,
            filter_functions=[OrderTypeApplicationFilter.BY_ORDER_TYPE],
            order_type=order_type,
        ).all()
        if not applications:
            raise EntryNotFoundError(f"No applications found for order type {order_type}")
        return applications

    def get_current_application_version_by_tag(self, tag: str) -> ApplicationVersion | None:
        """Return the current application version for an application tag."""
        application = self.get_application_by_tag(tag=tag)
        if not application:
            return None
        return apply_application_versions_filter(
            filter_functions=[
                ApplicationVersionFilter.BY_APPLICATION_ENTRY_ID,
                ApplicationVersionFilter.BY_VALID_FROM_BEFORE,
                ApplicationVersionFilter.ORDER_BY_VALID_FROM_DESC,
            ],
            application_versions=self._get_query(table=ApplicationVersion),
            application_entry_id=application.id,
            valid_from=dt.datetime.now(),
        ).first()

    def get_active_applications_by_prep_category(
        self, prep_category: SeqLibraryPrepCategory
    ) -> list[Application]:
        """Return all active applications by prep category."""
        return apply_application_filter(
            applications=self._get_query(table=Application),
            filter_functions=[
                ApplicationFilter.BY_PREP_CATEGORIES,
                ApplicationFilter.IS_NOT_ARCHIVED,
            ],
            prep_categories=[prep_category],
        ).all()

    def get_bed_version_by_file_name(self, bed_version_file_name: str) -> BedVersion:
        """Return bed version with file name."""
        return apply_bed_version_filter(
            bed_versions=self._get_query(table=BedVersion),
            bed_version_file_name=bed_version_file_name,
            filter_functions=[BedVersionFilter.BY_FILE_NAME],
        ).first()

    def get_bed_version_by_short_name(self, bed_version_short_name: str) -> BedVersion:
        """Return bed version with short name."""
        return apply_bed_version_filter(
            bed_versions=self._get_query(table=BedVersion),
            bed_version_short_name=bed_version_short_name,
            filter_functions=[BedVersionFilter.BY_SHORT_NAME],
        ).first()

    def get_bed_by_entry_id(self, bed_entry_id: int) -> Bed:
        """Get panel bed with bed entry id."""
        return apply_bed_filter(
            beds=self._get_query(table=Bed),
            filter_functions=[BedFilter.BY_ENTRY_ID],
            bed_entry_id=bed_entry_id,
        ).first()

    def get_bed_by_name(self, bed_name: str) -> Bed:
        """Get panel bed with bed name."""
        return apply_bed_filter(
            beds=self._get_query(table=Bed),
            filter_functions=[BedFilter.BY_NAME],
            bed_name=bed_name,
        ).first()

    def get_active_beds(self) -> Query:
        """Get all beds that are not archived."""
        bed_filter_functions: list[BedFilter] = [
            BedFilter.NOT_ARCHIVED,
            BedFilter.ORDER_BY_NAME,
        ]
        return apply_bed_filter(
            beds=self._get_query(table=Bed), filter_functions=bed_filter_functions
        )

    def get_customer_by_internal_id(self, customer_internal_id: str) -> Customer:
        """Return customer with customer id."""
        return apply_customer_filter(
            filter_functions=[CustomerFilter.BY_INTERNAL_ID],
            customers=self._get_query(table=Customer),
            customer_internal_id=customer_internal_id,
        ).first()

    def get_collaboration_by_internal_id(self, internal_id: str) -> Collaboration:
        """Fetch a customer group by internal id from the store."""
        return apply_collaboration_filter(
            collaborations=self._get_query(table=Collaboration),
            filter_functions=[CollaborationFilter.BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def get_organism_by_internal_id(self, internal_id: str) -> Organism:
        """Find an organism by internal id."""
        return apply_organism_filter(
            organisms=self._get_query(table=Organism),
            filter_functions=[OrganismFilter.BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def get_all_organisms(self) -> Query[Organism]:
        """Return all organisms ordered by organism internal id."""
        return self._get_query(table=Organism).order_by(Organism.internal_id)

    def get_customers(self) -> list[Customer]:
        """Return costumers."""
        return self._get_query(table=Customer).all()

    def get_panel_by_abbreviation(self, abbreviation: str) -> Panel:
        """Return a panel by abbreviation."""
        return apply_panel_filter(
            panels=self._get_query(table=Panel),
            filters=[PanelFilter.BY_ABBREVIATION],
            abbreviation=abbreviation,
        ).first()

    def get_panels(self) -> list[Panel]:
        """Returns all panels."""
        return self._get_query(table=Panel).order_by(Panel.abbrev).all()

    def get_user_by_email(self, email: str) -> User | None:
        """Return a user by email from the database."""
        return apply_user_filter(
            users=self._get_query(table=User),
            email=email,
            filter_functions=[UserFilter.BY_EMAIL],
        ).first()

    def get_user_by_entry_id(self, id: int) -> User | None:
        """Return a user by its entry id."""
        return apply_user_filter(
            users=self._get_query(table=User),
            user_id=id,
            filter_functions=[UserFilter.BY_ID],
        ).first()

    def is_user_associated_with_customer(self, user_id: int, customer_internal_id: str) -> bool:
        user: User | None = apply_user_filter(
            users=self._get_query(table=User),
            user_id=user_id,
            customer_internal_id=customer_internal_id,
            filter_functions=[UserFilter.BY_ID, UserFilter.BY_CUSTOMER_INTERNAL_ID],
        ).first()
        return bool(user)

    def is_customer_trusted(self, customer_internal_id: str) -> bool:
        customer: Customer | None = self.get_customer_by_internal_id(customer_internal_id)
        return bool(customer and customer.is_trusted)

    def customer_exists(self, customer_internal_id: str) -> bool:
        customer: Customer | None = self.get_customer_by_internal_id(customer_internal_id)
        return bool(customer)

    def get_samples_to_receive(self, external: bool = False) -> list[Sample]:
        """Return samples to receive."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.IS_NOT_RECEIVED,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        if external:
            records: Query = apply_application_filter(
                applications=records, filter_functions=[ApplicationFilter.IS_EXTERNAL]
            )
        else:
            records: Query = apply_application_filter(
                applications=records,
                filter_functions=[ApplicationFilter.IS_NOT_EXTERNAL],
            )
        return records.order_by(Sample.ordered_at).all()

    def get_samples_to_prepare(self) -> list[Sample]:
        """Return samples to prepare."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.IS_RECEIVED,
            SampleFilter.IS_NOT_PREPARED,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
            SampleFilter.IS_NOT_SEQUENCED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        records: Query = apply_application_filter(
            applications=records, filter_functions=[ApplicationFilter.IS_NOT_EXTERNAL]
        )

        return records.order_by(Sample.received_at).all()

    def get_samples_to_sequence(self) -> list[Sample]:
        """Return samples in sequencing."""
        records: Query = self._get_join_sample_application_version_query()
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.IS_PREPARED,
            SampleFilter.IS_NOT_SEQUENCED,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
        ]
        records: Query = apply_sample_filter(
            samples=records, filter_functions=sample_filter_functions
        )
        records: Query = apply_application_filter(
            applications=records, filter_functions=[ApplicationFilter.IS_NOT_EXTERNAL]
        )
        return records.order_by(Sample.prepared_at).all()

    def get_cases_with_analyzes(self) -> Query:
        """Return all cases in the database with an analysis."""
        return self._get_outer_join_cases_with_analyses_query()

    def get_cases_with_samples(self) -> Query:
        """Return all cases in the database with samples."""
        return self._get_join_cases_with_samples_query()

    def get_cases_to_analyze(self, workflow: Workflow = None, limit: int = None) -> list[Case]:
        """Returns a list if cases ready to be analyzed or set to be reanalyzed.
        1. Get cases to be analyzed using BE query
        2. Use the latest analysis for case to determine if the case is to be analyzed"""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.HAS_SEQUENCE,
            CaseFilter.PASSING_SEQUENCING_QC,
            CaseFilter.WITH_WORKFLOW,
            CaseFilter.FOR_ANALYSIS,
        ]
        cases = apply_case_filter(
            cases=self._get_case_query_for_analysis_start(),
            filter_functions=case_filter_functions,
            workflow=workflow,
        )
        sorted_and_truncated: Query = cases.order_by(Case.ordered_at).limit(limit)
        return sorted_and_truncated.all()

    def get_cases_to_compress(self, date_threshold: datetime) -> list[Case]:
        """Return all cases that are ready to be compressed by SPRING."""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.HAS_INACTIVE_ANALYSIS,
            CaseFilter.OLD_BY_CREATION_DATE,
            CaseFilter.IS_COMPRESSIBLE,
        ]
        return apply_case_filter(
            cases=self._get_query(table=Case),
            filter_functions=case_filter_functions,
            creation_date=date_threshold,
        ).all()

    def get_sample_by_entry_id(self, entry_id: int) -> Sample:
        """Return a sample by entry id."""
        sample: Sample | None = apply_sample_filter(
            filter_functions=[SampleFilter.BY_ENTRY_ID],
            samples=self._get_query(table=Sample),
            entry_id=entry_id,
        ).first()

        if not sample:
            LOG.error(f"Could not find sample with entry id {entry_id}")
            raise SampleNotFoundError(f"Could not find sample with entry id {entry_id}")
        return sample

    def get_sample_by_internal_id(self, internal_id: str) -> Sample | None:
        """Return a sample by lims id."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.BY_INTERNAL_ID],
            samples=self._get_query(table=Sample),
            internal_id=internal_id,
        ).first()

    def get_samples_by_identifier(self, object_type: str, identifier: str) -> list[Sample]:
        """Return all samples from a flow cell, case or sample id"""
        object_to_filter: dict[str, Callable] = {
            "sample": self.get_sample_by_internal_id,
            "case": self.get_samples_by_case_id,
            "flow_cell": self.get_samples_by_illumina_flow_cell,
        }
        samples: Sample | list[Sample] = object_to_filter[object_type](identifier)
        return samples if isinstance(samples, list) else [samples]

    def get_samples_by_internal_id(self, internal_id: str) -> list[Sample]:
        """Return all samples by lims id."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.BY_INTERNAL_ID],
            samples=self._get_query(table=Sample),
            internal_id=internal_id,
        ).all()

    def get_analyses_to_upload(self, workflow: Workflow | None = None) -> list[Analysis]:
        """Return analyses that have not been uploaded."""
        analysis_filter_functions: list[Callable] = [
            AnalysisFilter.WITH_WORKFLOW,
            AnalysisFilter.COMPLETED,
            AnalysisFilter.IS_NOT_UPLOADED,
            AnalysisFilter.VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions,
            analyses=self._get_join_analysis_case_query(),
            workflow=workflow,
        ).all()

    def get_analyses_to_clean(
        self, before: datetime = datetime.now(), workflow: Workflow | None = None
    ) -> list[Analysis]:
        """Return analyses that haven't been cleaned."""
        filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.IS_UPLOADED,
            AnalysisFilter.IS_NOT_CLEANED,
            AnalysisFilter.STARTED_AT_BEFORE,
            AnalysisFilter.CASE_ACTION_IS_NONE,
        ]
        if workflow:
            filter_functions.append(AnalysisFilter.WITH_WORKFLOW)
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_latest_analyses_for_cases_query(),
            workflow=workflow,
            started_at_date=before,
        ).all()

    def get_completed_analyses_for_workflow_started_at_before(
        self, workflow: Workflow, started_at_before: datetime
    ) -> list[Analysis]:
        """Return all analyses for a workflow started before a certain date."""
        filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.WITH_WORKFLOW,
            AnalysisFilter.STARTED_AT_BEFORE,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions,
            analyses=self._get_query(table=Analysis),
            workflow=workflow,
            started_at_date=started_at_before,
        ).all()

    def observations_to_upload(self, workflow: Workflow = None) -> Query:
        """Return observations that have not been uploaded."""
        case_filter_functions: list[CaseFilter] = [
            CaseFilter.WITH_LOQUSDB_SUPPORTED_WORKFLOW,
            CaseFilter.WITH_LOQUSDB_SUPPORTED_SEQUENCING_METHOD,
        ]
        records: Query = apply_case_filter(
            cases=self.get_cases_with_samples(),
            filter_functions=case_filter_functions,
            workflow=workflow,
        )
        return apply_sample_filter(
            filter_functions=[SampleFilter.WITHOUT_LOQUSDB_ID], samples=records
        )

    def observations_uploaded(self, workflow: Workflow = None) -> Query:
        """Return observations that have been uploaded."""
        records: Query = apply_case_filter(
            cases=self.get_cases_with_samples(),
            filter_functions=[CaseFilter.WITH_LOQUSDB_SUPPORTED_WORKFLOW],
            workflow=workflow,
        )
        records: Query = apply_sample_filter(
            filter_functions=[SampleFilter.WITH_LOQUSDB_ID], samples=records
        )
        return records

    def get_analyses(self) -> list[Analysis]:
        return self._get_query(table=Analysis).all()

    def get_analyses_to_deliver_for_pipeline(self, workflow: Workflow = None) -> list[Analysis]:
        """Return analyses that have been uploaded but not delivered."""
        analyses: Query = apply_sample_filter(
            samples=self._get_join_analysis_sample_family_query(),
            filter_functions=[SampleFilter.IS_NOT_DELIVERED],
        )
        filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.IS_NOT_UPLOADED,
            AnalysisFilter.WITH_WORKFLOW,
            AnalysisFilter.ORDER_BY_UPLOADED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=filter_functions, analyses=analyses, workflow=workflow
        ).all()

    def analyses_to_delivery_report(self, workflow: Workflow | None = None) -> Query:
        """Return analyses that need a delivery report to be regenerated."""
        records: Query = apply_case_filter(
            cases=self._get_join_analysis_case_query(),
            filter_functions=[CaseFilter.REPORT_SUPPORTED],
        )
        analysis_filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.REPORT_BY_WORKFLOW,
            AnalysisFilter.WITHOUT_DELIVERY_REPORT,
            AnalysisFilter.VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions, analyses=records, workflow=workflow
        )

    def analyses_to_upload_delivery_reports(self, workflow: Workflow = None) -> Query:
        """Return analyses that need a delivery report to be uploaded."""
        records: Query = apply_case_filter(
            cases=self._get_join_analysis_case_query(),
            filter_functions=[CaseFilter.WITH_SCOUT_DELIVERY],
        )
        analysis_filter_functions: list[Callable] = [
            AnalysisFilter.COMPLETED,
            AnalysisFilter.REPORT_BY_WORKFLOW,
            AnalysisFilter.WITH_DELIVERY_REPORT,
            AnalysisFilter.IS_NOT_UPLOADED,
            AnalysisFilter.VALID_IN_PRODUCTION,
            AnalysisFilter.ORDER_BY_COMPLETED_AT,
        ]
        return apply_analysis_filter(
            filter_functions=analysis_filter_functions, analyses=records, workflow=workflow
        )

    def get_samples_to_deliver(self) -> list[Sample]:
        """Return all samples not delivered."""
        records = self._get_query(table=Sample)
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.IS_SEQUENCED,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
            SampleFilter.IS_NOT_DELIVERED,
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
            SampleFilter.HAS_NO_INVOICE_ID,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
        ]

        records: Query = apply_sample_filter(
            filter_functions=sample_filter_functions,
            samples=records,
        )
        return records.all()

    def get_samples_not_down_sampled(self) -> list[Sample]:
        """Return all samples that have not been down sampled."""
        return apply_sample_filter(
            filter_functions=[SampleFilter.IS_NOT_DOWN_SAMPLED],
            samples=self._get_query(table=Sample),
        ).all()

    def get_samples_to_invoice_query(self) -> Query:
        """Return all samples that should be invoiced."""
        sample_filter_functions: list[SampleFilter] = [
            SampleFilter.IS_DELIVERED,
            SampleFilter.HAS_NO_INVOICE_ID,
            SampleFilter.DO_INVOICE,
            SampleFilter.IS_NOT_DOWN_SAMPLED,
        ]
        return apply_sample_filter(
            filter_functions=sample_filter_functions,
            samples=self._get_query(table=Sample),
        )

    def get_pools_to_invoice_query(self) -> Query:
        """Return all pools that should be invoiced."""
        pool_filter_functions: list[PoolFilter] = [
            PoolFilter.IS_DELIVERED,
            PoolFilter.WITHOUT_INVOICE_ID,
            PoolFilter.DO_INVOICE,
        ]
        return apply_pool_filter(
            filter_functions=pool_filter_functions,
            pools=self._get_query(table=Pool),
        )

    def get_samples_to_invoice_for_customer(self, customer: Customer = None) -> list[Sample]:
        """Return all samples that should be invoiced for a customer."""
        return apply_sample_filter(
            samples=self.get_samples_to_invoice_query(),
            filter_functions=[SampleFilter.BY_CUSTOMER],
            customer=customer,
        ).all()

    def get_pools_to_invoice_for_customer(self, customer: Customer = None) -> list[Pool]:
        """Return all pools for a customer that should be invoiced."""
        return apply_pool_filter(
            filter_functions=[PoolFilter.BY_CUSTOMER],
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
            filter_functions=[PoolFilter.IS_NOT_RECEIVED], pools=self._get_query(table=Pool)
        ).all()

    def get_all_pools_to_deliver(self) -> list[Pool]:
        """Return all pools that are received but have not yet been delivered."""
        records = self._get_query(table=Pool)
        pool_filter_functions: list[PoolFilter] = [
            PoolFilter.IS_RECEIVED,
            PoolFilter.IS_NOT_DELIVERED,
        ]

        records: Query = apply_pool_filter(
            filter_functions=pool_filter_functions,
            pools=records,
        )
        return records.all()

    def get_orders(self, orders_params: OrderQueryParams) -> tuple[list[Order], int]:
        """Filter, sort and paginate orders based on the provided request."""
        orders: Query = self._get_join_order_case_query()
        if len(orders_params.workflows) > 0:
            orders: Query = apply_case_filter(
                cases=orders,
                filter_functions=[CaseFilter.BY_WORKFLOWS],
                workflows=orders_params.workflows,
            )
        orders = orders.distinct()
        orders: Query = apply_order_filters(
            orders=orders,
            filters=[OrderFilter.BY_SEARCH, OrderFilter.BY_OPEN],
            search=orders_params.search,
            is_open=orders_params.is_open,
        )
        total_count: int = orders.count()
        orders: list[Order] = self.sort_and_paginate_orders(
            orders=orders, orders_params=orders_params
        )
        return orders, total_count

    def sort_and_paginate_orders(
        self, orders: Query, orders_params: OrderQueryParams
    ) -> list[Order]:
        return apply_order_filters(
            orders=orders,
            filters=[OrderFilter.SORT, OrderFilter.PAGINATE],
            sort_field=orders_params.sort_field,
            sort_order=orders_params.sort_order,
            page=orders_params.page,
            page_size=orders_params.page_size,
        ).all()

    def get_orders_by_ids(self, order_ids: list[int]) -> list[Order]:
        """Return all orders with the provided ids."""
        return apply_order_filters(
            orders=self._get_query(Order),
            filters=[OrderFilter.BY_IDS],
            ids=order_ids,
        ).all()

    def get_order_by_id(self, order_id: int) -> Order:
        """Returns the entry in Order matching the given id."""
        orders: Query = self._get_query(table=Order)
        order_filter_functions: list[Callable] = [OrderFilter.BY_ID]
        orders: Query = apply_order_filters(
            orders=orders, filters=order_filter_functions, id=order_id
        )
        if not (order := orders.first()):
            raise OrderNotFoundError(f"Order with ID {order_id} not found.")
        return order

    def get_order_by_ticket_id(self, ticket_id: int) -> Order | None:
        """Returns the entry in Order matching the given id."""
        orders: Query = self._get_query(table=Order)
        order_filter_functions: list[Callable] = [OrderFilter.BY_TICKET_ID]
        orders: Query = apply_order_filters(
            orders=orders, filters=order_filter_functions, ticket_id=ticket_id
        )
        return orders.first()

    def get_case_not_received_count(self, order_id: int, cases_to_exclude: list[str]) -> int:
        filters: list[CaseSampleFilter] = [
            CaseSampleFilter.BY_ORDER,
            CaseSampleFilter.CASES_WITH_SAMPLES_NOT_RECEIVED,
            CaseSampleFilter.EXCLUDE_CASES,
        ]
        case_samples: Query = self._join_sample_and_case()
        return apply_case_sample_filter(
            case_samples=case_samples,
            filter_functions=filters,
            order_id=order_id,
            cases_to_exclude=cases_to_exclude,
        ).count()

    def get_case_in_preparation_count(self, order_id: int, cases_to_exclude: list[str]) -> int:
        filters: list[CaseFilter] = [
            CaseSampleFilter.BY_ORDER,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_RECEIVED,
            CaseSampleFilter.CASES_WITH_SAMPLES_NOT_PREPARED,
            CaseSampleFilter.EXCLUDE_CASES,
        ]
        case_samples: Query = self._join_sample_and_case()
        return apply_case_sample_filter(
            case_samples=case_samples,
            filter_functions=filters,
            order_id=order_id,
            cases_to_exclude=cases_to_exclude,
        ).count()

    def get_case_in_sequencing_count(self, order_id: int, cases_to_exclude: list[str]) -> int:
        filters: list[CaseSampleFilter] = [
            CaseSampleFilter.BY_ORDER,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_RECEIVED,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_PREPARED,
            CaseSampleFilter.CASES_WITH_SAMPLES_NOT_SEQUENCED,
            CaseSampleFilter.EXCLUDE_CASES,
        ]
        case_samples: Query = self._join_sample_and_case()
        return apply_case_sample_filter(
            case_samples=case_samples,
            filter_functions=filters,
            order_id=order_id,
            cases_to_exclude=cases_to_exclude,
        ).count()

    def get_case_failed_sequencing_count(self, order_id: int, cases_to_exclude: list[str]) -> int:
        filters: list[CaseSampleFilter] = [
            CaseSampleFilter.BY_ORDER,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_RECEIVED,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_PREPARED,
            CaseSampleFilter.CASES_WITH_ALL_SAMPLES_SEQUENCED,
            CaseSampleFilter.CASES_FAILED_SEQUENCING_QC,
            CaseSampleFilter.EXCLUDE_CASES,
        ]
        case_samples: Query = self._join_sample_and_case()
        return apply_case_sample_filter(
            case_samples=case_samples,
            filter_functions=filters,
            order_id=order_id,
            cases_to_exclude=cases_to_exclude,
        ).count()

    def get_illumina_flow_cell_by_internal_id(self, internal_id: str) -> IlluminaFlowCell:
        """Return a flow cell by internal id."""
        flow_cell: IlluminaFlowCell | None = apply_illumina_flow_cell_filters(
            filter_functions=[IlluminaFlowCellFilter.BY_INTERNAL_ID],
            flow_cells=self._get_query(table=IlluminaFlowCell),
            internal_id=internal_id,
        ).first()
        if not flow_cell:
            raise EntryNotFoundError(
                f"Could not find Illumina flow cell with internal id {internal_id}"
            )
        return flow_cell

    def get_cases_for_sequencing_qc(self) -> list[Case]:
        """Return all cases that are ready for sequencing QC."""
        query = (
            self._get_query(table=Case)
            .join(Case.links)
            .join(CaseSample.sample)
            .join(ApplicationVersion)
            .join(Application)
        )
        return apply_case_filter(
            cases=query,
            filter_functions=[
                CaseFilter.PENDING_OR_FAILED_SEQUENCING_QC,
                CaseFilter.HAS_SEQUENCE,
            ],
        ).all()

    def is_application_archived(self, application_tag: str) -> bool:
        application: Application | None = self.get_application_by_tag(application_tag)
        return application and application.is_archived

    def does_gene_panel_exist(self, abbreviation: str) -> bool:
        return bool(self.get_panel_by_abbreviation(abbreviation))

    def get_pac_bio_smrt_cell_by_internal_id(self, internal_id: str) -> PacbioSMRTCell:
        return apply_pac_bio_smrt_cell_filters(
            filter_functions=[PacBioSMRTCellFilter.BY_INTERNAL_ID],
            smrt_cells=self._get_query(table=PacbioSMRTCell),
            internal_id=internal_id,
        ).first()

    def get_case_ids_with_sample(self, sample_id: int) -> list[str]:
        """Return all case ids with a sample."""
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        return [link.case.internal_id for link in sample.links] if sample else []

    def get_case_ids_for_samples(self, sample_ids: list[int]) -> list[str]:
        case_ids: list[str] = []
        for sample_id in sample_ids:
            case_ids.extend(self.get_case_ids_with_sample(sample_id))
        return list(set(case_ids))

    def sample_exists_with_different_sex(
        self,
        customer_internal_id: str,
        subject_id: str,
        sex: SexEnum,
    ) -> bool:
        samples: list[Sample] = self.get_samples_by_customer_and_subject_id(
            customer_internal_id=customer_internal_id,
            subject_id=subject_id,
        )
        for sample in samples:
            if sample.sex == SexEnum.unknown:
                continue
            if sample.sex != sex:
                return True
        return False

    def _get_related_samples_query(
        self,
        sample: Sample,
        prep_categories: list[SeqLibraryPrepCategory],
        collaborators: set[Customer],
    ) -> Query:
        """
        Returns a sample query with the same subject_id, tumour status and within the collaborators of the given
        sample and within the given list of prep categories.
        Raises:
            CgDataError if the number of samples matching the criteria is not 1
        """

        sample_application_version_query: Query = self._get_join_sample_application_version_query()

        sample_application_version_query: Query = apply_application_filter(
            applications=sample_application_version_query,
            prep_categories=prep_categories,
            filter_functions=[ApplicationFilter.BY_PREP_CATEGORIES],
        )

        samples: Query = apply_sample_filter(
            samples=sample_application_version_query,
            subject_id=sample.subject_id,
            is_tumour=sample.is_tumour,
            customer_entry_ids=[customer.id for customer in collaborators],
            filter_functions=[
                SampleFilter.BY_SUBJECT_ID,
                SampleFilter.BY_TUMOUR,
                SampleFilter.BY_CUSTOMER_ENTRY_IDS,
            ],
        )
        if samples.count() != 1:
            samples: list[Sample] = samples.all()
            raise CgDataError(
                f"No unique DNA sample could be found: found {len(samples)} samples: {[sample.internal_id for sample in samples]}"
            )
        return samples

    def get_uploaded_related_dna_cases(self, rna_case: Case) -> list[Case]:
        """
        Finds all cases fulfilling the following criteria:
        1. The case should be uploaded
        2. The case should belong to a customer within the collaboration of the provided case's
        3. It should contain exactly one DNA sample matching one of the provided case's RNA samples in the following way:
            1. The DNA sample and the RNA sample should have matching subject_ids
            2. The DNA sample and the RNA sample should have matching is_tumour
        4. The DNA sample found in 3. should also:
            1. Have an application within a DNA prep category
            2. Belong to a customer within the provided collaboration

        Raises:
            CgDataError if no related DNA cases are found
        """

        related_dna_cases: list[Case] = []
        collaborators: set[Customer] = rna_case.customer.collaborators
        for rna_sample in rna_case.samples:
            uploaded_dna_cases: list[Case] = self._get_related_uploaded_cases_for_rna_sample(
                rna_sample=rna_sample, collaborators=collaborators
            )
            # Only add unique DNA cases to the list since we are going from RNA samples to DNA cases in the loop above
            for case in uploaded_dna_cases:
                if case not in related_dna_cases:
                    related_dna_cases.append(case)
        if not related_dna_cases:
            raise CgDataError(
                f"No matching uploaded DNA cases for case {rna_case.internal_id} ({rna_case.name})."
            )
        return related_dna_cases

    def _get_related_uploaded_cases_for_rna_sample(
        self, rna_sample: Sample, collaborators: set[Customer]
    ) -> list[Case]:
        if not rna_sample.subject_id:
            raise CgDataError(
                f"Failed to link RNA sample {rna_sample.internal_id} to DNA samples - subject_id field is empty."
            )

        related_dna_samples_query: Query = self._get_related_samples_query(
            sample=rna_sample,
            prep_categories=DNA_PREP_CATEGORIES,
            collaborators=collaborators,
        )
        customer_ids: list[int] = [customer.id for customer in collaborators]
        return self._get_uploaded_dna_cases(
            sample_query=related_dna_samples_query, customer_ids=customer_ids
        )

    def _get_uploaded_dna_cases(self, sample_query: Query, customer_ids: list[int]) -> list[Case]:
        """Filters the provided sample_query on the customer_ids, DNA workflows supporting
        Scout uploads and on cases having an uploaded analysis. Returns the matching cases."""
        dna_samples_cases_analysis_query: Query = (
            sample_query.join(Sample.links).join(CaseSample.case).join(Analysis)
        )
        dna_samples_cases_analysis_query: Query = apply_case_filter(
            cases=dna_samples_cases_analysis_query,
            workflows=DNA_WORKFLOWS_WITH_SCOUT_UPLOAD,
            customer_entry_ids=customer_ids,
            filter_functions=[
                CaseFilter.BY_WORKFLOWS,
                CaseFilter.BY_CUSTOMER_ENTRY_IDS,
            ],
        )
        uploaded_dna_cases: list[Case] = (
            apply_analysis_filter(
                analyses=dna_samples_cases_analysis_query,
                filter_functions=[AnalysisFilter.IS_UPLOADED],
            )
            .with_entities(Case)
            .all()
        )
        return uploaded_dna_cases

    def get_related_dna_cases_with_samples(self, rna_case: Case) -> list[RNADNACollection]:
        """
        Finds all cases fulfilling the following criteria:
        1. The case should be uploaded
        2. The case should belong to a customer within the collaboration of the provided case's
        3. It should contain exactly one DNA sample matching one of the provided case's RNA samples in the following way:
            1. The DNA sample and the RNA sample should have matching subject_ids
            2. The DNA sample and the RNA sample should have matching is_tumour
        4. The DNA sample found in 3. should also:
            1. Have an application within a DNA prep category
            2. Belong to a customer within the provided collaboration

        The cases are bundled by the DNA sample found in 3.
        """
        collaborators: set[Customer] = rna_case.customer.collaborators
        collaborator_ids: list[int] = [collaborator.id for collaborator in collaborators]
        rna_dna_collections: list[RNADNACollection] = []
        for sample in rna_case.samples:
            if not sample.subject_id:
                raise CgDataError(
                    f"Failed to link RNA sample {sample.internal_id} to DNA samples - subject_id field is empty."
                )
            related_dna_samples: Query = self._get_related_samples_query(
                sample=sample, prep_categories=DNA_PREP_CATEGORIES, collaborators=collaborators
            )
            dna_sample_name: str = related_dna_samples.first().name
            dna_cases: list[Case] = self._get_uploaded_dna_cases(
                sample_query=related_dna_samples, customer_ids=collaborator_ids
            )
            dna_case_ids: list[str] = [case.internal_id for case in dna_cases]
            collection = RNADNACollection(
                rna_sample_id=sample.internal_id,
                dna_sample_name=dna_sample_name,
                dna_case_ids=dna_case_ids,
            )
            rna_dna_collections.append(collection)
        return rna_dna_collections

    def get_pacbio_sample_sequencing_metrics(
        self, sample_id: str | None, smrt_cell_ids: list[str] | None
    ) -> list[PacbioSampleSequencingMetrics]:
        """
        Fetches data from PacbioSampleSequencingMetrics filtered on sample_internal_id and/or smrt_cell_id.
        """
        sequencing_metrics: Query = (
            self._get_query(table=PacbioSampleSequencingMetrics)
            .join(Sample)
            .join(InstrumentRun)
            .join(RunDevice)
        )
        if sample_id:
            sequencing_metrics = sequencing_metrics.filter(Sample.internal_id == sample_id)
        if smrt_cell_ids:
            sequencing_metrics = sequencing_metrics.filter(RunDevice.internal_id.in_(smrt_cell_ids))
        return sequencing_metrics.all()

    def get_pacbio_sequencing_runs_by_run_name(self, run_name: str) -> list[PacbioSequencingRun]:
        """
        Fetches data from PacbioSequencingRunDTO filtered on run name.
        Raises:
            EntryNotFoundError if no sequencing runs are found for the run name
        """
        runs: Query = self._get_query(table=PacbioSequencingRun)
        runs = runs.filter(PacbioSequencingRun.run_name == run_name)
        if runs.count() == 0:
            raise EntryNotFoundError(f"Could not find any sequencing runs for {run_name}")
        return runs.all()

    def get_case_priority(self, case_id: str) -> SlurmQos:
        """Get case priority."""
        case: Case = self.get_case_by_internal_id(case_id)
        return SlurmQos(case.slurm_priority)

    def get_case_workflow(self, case_id: str) -> Workflow:
        """Get case workflow."""
        case: Case = self.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

    def is_sample_name_used(self, sample: Sample, customer_entry_id: int) -> bool:
        """Check if a sample name is already used by the customer"""
        if self.get_sample_by_customer_and_name(
            customer_entry_id=[customer_entry_id], sample_name=sample.name
        ):
            return True
        return False
