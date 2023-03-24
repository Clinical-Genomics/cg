"""Handler to find business data objects."""
import datetime as dt
import logging
from typing import List, Optional, Iterator, Union

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.constants.constants import PrepCategory, SampleType
from cg.constants.indexes import ListIndexes
from cg.exc import CaseNotFoundError
from cg.store.api.base import BaseHandler
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter

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
)

from cg.store.filters.status_invoice_filters import apply_invoice_filter, InvoiceFilter
from cg.store.filters.status_pool_filters import apply_pool_filter, PoolFilter
from cg.store.filters.status_flow_cell_filters import apply_flow_cell_filter, FlowCellFilter
from cg.store.filters.status_case_sample_filters import apply_case_sample_filter, CaseSampleFilter
from cg.store.filters.status_sample_filters import apply_sample_filter, SampleFilter


LOG = logging.getLogger(__name__)


class FindBusinessDataHandler(BaseHandler):
    """Contains methods to find business data model instances"""

    def analyses(self, *, family: Family = None, before: dt.datetime = None) -> Query:
        """Fetch multiple analyses."""
        records = self.Analysis.query
        if family:
            query_family = family
            records = records.filter(Analysis.family == query_family)
        if before:
            subq = (
                self.Analysis.query.join(Analysis.family)
                .filter(Analysis.started_at < before)
                .group_by(Family.id)
                .with_entities(
                    Analysis.family_id,
                    func.max(Analysis.started_at).label("started_at"),
                )
                .subquery()
            )
            records = records.join(
                subq,
                and_(
                    self.Analysis.family_id == subq.c.family_id,
                    self.Analysis.started_at == subq.c.started_at,
                ),
            ).filter(Analysis.started_at < before)
        return records

    def has_active_cases_for_sample(self, internal_id: str) -> bool:
        """Check if there are any active cases for a sample"""
        sample = self.get_sample_by_internal_id(internal_id=internal_id)
        for family_sample in sample.links:
            case_action = self.get_case_action(sample=family_sample)
            if case_action in ["analyze", "running"]:
                return True
        return False

    def get_case_action(self, sample: FamilySample) -> str:
        """Get the action of a case."""
        return self.get_case_by_internal_id(
            internal_id=self.Family.query.filter(Family.id == sample.family_id).first().internal_id
        ).action

    def get_application_by_case(self, case_id: str) -> Application:
        """Return the application of a case."""

        return (
            self.get_case_by_internal_id(internal_id=case_id)
            .links[ListIndexes.FIRST.value]
            .sample.application_version.application
        )

    def analyses_ready_for_vogue_upload(
        self,
        completed_after: Optional[dt.date],
        completed_before: Optional[dt.date],
    ) -> Query:
        """Fetch all cases with a finished analysis that has not been uploaded to Vogue.
        Optionally fetch those cases finished before and/or after a specified date"""
        records = self.latest_analyses().filter(Analysis.uploaded_to_vogue_at.is_(None))

        if completed_after:
            records = records.filter(Analysis.completed_at > completed_after)
        if completed_before:
            records = records.filter(Analysis.completed_at < completed_before)

        return records

    def latest_analyses(self) -> Query:
        """Fetch latest analysis for all cases."""

        records = self.Analysis.query
        sub_query = (
            self.Analysis.query.join(Analysis.family)
            .group_by(Family.id)
            .with_entities(Analysis.family_id, func.max(Analysis.started_at).label("started_at"))
            .subquery()
        )
        records = records.join(
            sub_query,
            and_(
                self.Analysis.family_id == sub_query.c.family_id,
                self.Analysis.started_at == sub_query.c.started_at,
            ),
        )
        return records

    def analysis(self, family: Family, started_at: dt.datetime) -> Analysis:
        """Fetch an analysis."""
        return self.Analysis.query.filter_by(family=family, started_at=started_at).first()

    def deliveries(self) -> Query:
        """Fetch all deliveries."""
        return self.Delivery.query

    def families(
        self,
        *,
        action: Optional[str] = None,
        data_analysis: Optional[str] = None,
        customers: List[Customer] = None,
        enquiry: Optional[str] = None,
    ) -> Query:
        """Fetch families."""

        records = self.Family.query

        if customers:
            customer_ids = [customer.id for customer in customers]
            records = records.filter(Family.customer_id.in_(customer_ids))

        records = (
            records.filter(
                or_(
                    Family.name.like(f"%{enquiry}%"),
                    Family.internal_id.like(f"%{enquiry}%"),
                )
            )
            if enquiry
            else records
        )
        records = records.filter_by(action=action) if action else records
        records = records.filter_by(data_analysis=data_analysis) if data_analysis else records
        return records.order_by(Family.created_at.desc())

    def family_samples(self, family_id: str) -> List[FamilySample]:
        """Return the case-sample links associated with a case."""
        return apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_SAMPLES_ASSOCIATED_WITH_CASE],
            case_id=family_id,
            case_samples=self._get_join_case_sample_query(),
        ).all()

    def get_sample_cases(self, sample_id: str) -> Query:
        """Return the case-sample links associated with a sample."""
        return apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_CASES_ASSOCIATED_WITH_SAMPLE],
            sample_id=sample_id,
            case_samples=self._get_join_case_sample_query(),
        )

    def get_cases_from_sample(self, sample_entry_id: str) -> Query:
        """Return cases related to a given sample."""
        return apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_CASES_ASSOCIATED_WITH_SAMPLE_BY_ENTRY_ID],
            sample_entry_id=sample_entry_id,
            case_samples=self._get_join_case_sample_query(),
        )

    def filter_cases_with_samples(self, case_ids: List[str]) -> List[str]:
        """Return case id:s associated with samples."""
        cases_with_samples = set()
        for case_id in case_ids:
            case: Family = self.get_case_by_internal_id(internal_id=case_id)
            if case and case.links:
                cases_with_samples.add(case_id)
        return list(cases_with_samples)

    def get_cases_from_ticket(self, ticket: str) -> Query:
        return self.Family.query.filter(Family.tickets.contains(ticket))

    def get_customer_id_from_ticket(self, ticket: str) -> str:
        """Returns the customer related to given ticket"""
        return (
            self.Family.query.filter(Family.tickets.contains(ticket)).first().customer.internal_id
        )

    def get_samples_from_ticket(self, ticket: str) -> List[Sample]:
        return self._get_join_sample_family_query().filter(Family.tickets.contains(ticket)).all()

    def get_latest_ticket_from_case(self, case_id: str) -> str:
        """Returns the ticket from the most recent sample in a case"""
        return self.get_case_by_internal_id(internal_id=case_id).latest_ticket

    def get_latest_flow_cell_on_case(self, family_id: str) -> Flowcell:
        """Fetch the latest sequenced flow cell related to a sample on a case."""
        flow_cells_on_case: List[Flowcell] = list(
            self.get_flow_cells_by_case(case=self.get_case_by_internal_id(internal_id=family_id))
        )
        flow_cells_on_case.sort(key=lambda flow_cell: flow_cell.sequenced_at)
        return flow_cells_on_case[-1]

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

    def get_sequenced_samples(self, family_id: str) -> List[Sample]:
        """Get sequenced samples by family_id."""

        samples: List[Sample] = self.get_samples_by_case_id(family_id)
        return [sample for sample in samples if sample.sequencing_qc]

    def find_family(self, customer: Customer, name: str) -> Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(customer=customer, name=name).first()

    def find_family_by_name(self, name: str) -> Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(name=name).first()

    def find_samples(self, customer: Customer, name: str) -> Query:
        """Find samples within a customer."""
        return self._get_query(table=Sample).filter_by(customer=customer, name=name)

    def get_flow_cell(self, flow_cell_id: str) -> Flowcell:
        """Return flow cell by flow cell id."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_id=flow_cell_id,
            filter_functions=[FlowCellFilter.GET_BY_ID],
        ).first()

    def get_flow_cell_by_enquiry(self, flow_cell_id_enquiry: str) -> Flowcell:
        """Return flow cell enquiry."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_id=flow_cell_id_enquiry,
            filter_functions=[FlowCellFilter.GET_BY_ID_AND_ENQUIRY],
        ).first()

    def get_flow_cells(self) -> List[Flowcell]:
        """Return all flow cells."""
        return self._get_query(table=Flowcell)

    def get_flow_cells_by_statuses(self, flow_cell_statuses: List[str]) -> Optional[List[Flowcell]]:
        """Return flow cells with supplied statuses."""
        return apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=[FlowCellFilter.GET_WITH_STATUSES],
        )

    def get_flow_cell_by_enquiry_and_status(
        self, flow_cell_statuses: List[str], flow_cell_id_enquiry: str
    ) -> List[Flowcell]:
        """Return flow cell enquiry snd status."""
        filter_functions: List[FlowCellFilter] = [
            FlowCellFilter.GET_WITH_STATUSES,
            FlowCellFilter.GET_BY_ID_AND_ENQUIRY,
        ]
        flow_cells: List[Flowcell] = apply_flow_cell_filter(
            flow_cells=self._get_query(table=Flowcell),
            flow_cell_id=flow_cell_id_enquiry,
            flow_cell_statuses=flow_cell_statuses,
            filter_functions=filter_functions,
        )
        return flow_cells

    def get_flow_cells_by_case(self, case: Family) -> Optional[List[Flowcell]]:
        """Return flow cells for case."""
        return apply_flow_cell_filter(
            flow_cells=self._get_join_flow_cell_sample_links_query(),
            filter_functions=[FlowCellFilter.GET_BY_CASE],
            case=case,
        )

    def get_samples_from_flow_cell(self, flow_cell_id: str) -> Optional[List[Sample]]:
        """Return samples present on flow cell."""
        flow_cell: Flowcell = self.get_flow_cell(flow_cell_id=flow_cell_id)
        if flow_cell:
            return flow_cell.samples

    def is_all_flow_cells_on_disk(self, case_id: str) -> bool:
        """Check if flow cells are on disk for sample before starting the analysis.
        Flow cells not on disk will be requested.
        """
        flow_cells: Optional[List[Flowcell]] = list(
            self.get_flow_cells_by_case(case=self.get_case_by_internal_id(internal_id=case_id))
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
        self.commit()
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

    def link(self, family_id: str, sample_id: str) -> FamilySample:
        """Find a link between a family and a sample."""
        return (
            self.FamilySample.query.join(FamilySample.family, FamilySample.sample)
            .filter(Family.internal_id == family_id, Sample.internal_id == sample_id)
            .first()
        )

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

    def get_samples(self) -> List[Sample]:
        """Return all samples."""
        return self._get_query(table=Sample).order_by(Sample.created_at.desc()).all()

    def get_samples_by_name_pattern(self, name_pattern: str) -> List[Sample]:
        """Return all samples with a name fitting the pattern."""
        return apply_sample_filter(
            samples=self._get_query(table=Sample),
            name_pattern=name_pattern,
            filter_functions=[SampleFilter.FILTER_BY_NAME_PATTERN],
        ).all()

    def get_samples_by_customer_id_and_pattern(
        self, *, customers: Optional[List[Customer]] = None, enquiry: str = None
    ) -> List[Sample]:
        samples: Query = self._get_query(table=Sample)
        customer_ids = None
        filter_functions: List[SampleFilter] = []
        if customers:
            customer_ids: List[int] = [customer.id for customer in customers]
            filter_functions.append(SampleFilter.FILTER_BY_CUSTOMER_ID)
        if enquiry:
            filter_functions.extend(
                [SampleFilter.FILTER_BY_INTERNAL_ID_PATTERN, SampleFilter.FILTER_BY_NAME_PATTERN]
            )
        filter_functions.append(SampleFilter.ORDER_BY_CREATED_AT_DESC)
        return apply_sample_filter(
            samples=samples,
            customer_ids=customer_ids,
            name_pattern=enquiry,
            internal_id_pattern=enquiry,
            filter_functions=filter_functions,
        ).all()

    def get_samples_by_subject_id(self, customer_id: str, subject_id: str) -> List[Sample]:
        """Get samples of customer with given subject_id or subject_id and is_tumour."""
        query: Query = self._get_join_sample_and_customer_query().filter(
            Customer.internal_id == customer_id, Sample.subject_id == subject_id
        )
        return query.all()

    def get_samples_by_subject_id_and_is_tumour(
        self, customer_id: str, subject_id: str, is_tumour: bool
    ) -> List[Sample]:
        """Get samples of customer with given subject_id and is_tumour."""
        samples: Query = self._get_join_sample_and_customer_query().filter(
            Customer.internal_id == customer_id, Sample.subject_id == subject_id
        )

        if is_tumour:
            return apply_sample_filter(
                samples=samples, filter_functions=[SampleFilter.FILTER_IS_TUMOUR]
            ).all()
        else:
            return apply_sample_filter(
                samples=samples, filter_functions=[SampleFilter.FILTER_IS_NOT_TUMOUR]
            ).all()

    def get_samples_by_any_id(self, **identifiers: dict) -> Query:
        records = self._get_query(table=Sample)

        for identifier_name, identifier_value in identifiers.items():
            identifier = getattr(Sample, identifier_name)
            records = records.filter(identifier.contains(identifier_value))

        return records.order_by(Sample.internal_id.desc())

    def get_sample_by_name(self, name: str) -> Sample:
        """Get sample by name."""
        samples = self._get_query(table=Sample)
        return apply_sample_filter(
            samples=samples, filter_functions=[SampleFilter.FILTER_BY_SAMPLE_NAME], name=name
        ).first()

    def get_samples_by_type(self, case_id: str, sample_type: SampleType) -> Optional[List[Sample]]:
        """Get samples given a tissue type."""
        samples: Query = apply_case_sample_filter(
            filter_functions=[CaseSampleFilter.GET_SAMPLES_ASSOCIATED_WITH_CASE],
            case_samples=self._get_join_sample_family_query(),
            case_id=case_id,
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
