"""Handler to find business data objects"""
import datetime as dt
from typing import List, Optional, Set

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query, load_only
from cg.constants.constants import PrepCategory
from cg.constants.indexes import ListIndexes
from cg.store import models
from cg.store.api.base import BaseHandler
from cgmodels.cg.constants import Pipeline

from cg.store.models import Flowcell
from cg.store.status_flow_cell_filters import apply_flow_cell_filter


class FindBusinessDataHandler(BaseHandler):
    """Contains methods to find business data model instances"""

    def analyses(self, *, family: models.Family = None, before: dt.datetime = None) -> Query:
        """Fetch multiple analyses."""
        records = self.Analysis.query
        if family:
            query_family = family
            records = records.filter(models.Analysis.family == query_family)
        if before:
            subq = (
                self.Analysis.query.join(models.Analysis.family)
                .filter(models.Analysis.started_at < before)
                .group_by(models.Family.id)
                .with_entities(
                    models.Analysis.family_id,
                    func.max(models.Analysis.started_at).label("started_at"),
                )
                .subquery()
            )
            records = records.join(
                subq,
                and_(
                    self.Analysis.family_id == subq.c.family_id,
                    self.Analysis.started_at == subq.c.started_at,
                ),
            ).filter(models.Analysis.started_at < before)
        return records

    def active_sample(self, internal_id: str) -> bool:
        """Check if there are any active cases for a sample"""
        sample: models.Sample = self.sample(internal_id=internal_id)
        if any(
            [
                self.family(
                    internal_id=self.Family.query.filter(
                        models.Family.id == family_sample.family_id
                    )
                    .first()
                    .internal_id
                ).action
                == "analyze"
                or self.family(
                    internal_id=self.Family.query.filter(
                        models.Family.id == family_sample.family_id
                    )
                    .first()
                    .internal_id
                ).action
                == "running"
                for family_sample in sample.links
            ]
        ):
            return True
        return False

    def get_application_by_case(self, case_id: str) -> models.Application:
        """Return the application of a case."""

        return (
            self.family(case_id)
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
        records = self.latest_analyses().filter(models.Analysis.uploaded_to_vogue_at.is_(None))

        if completed_after:
            records = records.filter(models.Analysis.completed_at > completed_after)
        if completed_before:
            records = records.filter(models.Analysis.completed_at < completed_before)

        return records

    def latest_analyses(self) -> Query:
        """Fetch latest analysis for all cases."""

        records = self.Analysis.query
        sub_query = (
            self.Analysis.query.join(models.Analysis.family)
            .group_by(models.Family.id)
            .with_entities(
                models.Analysis.family_id, func.max(models.Analysis.started_at).label("started_at")
            )
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

    def analysis(self, family: models.Family, started_at: dt.datetime) -> models.Analysis:
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
        customers: List[models.Customer] = None,
        enquiry: Optional[str] = None,
    ) -> Query:
        """Fetch families."""

        records = self.Family.query

        if customers:
            customer_ids = [customer.id for customer in customers]
            records = records.filter(models.Family.customer_id.in_(customer_ids))

        records = (
            records.filter(
                or_(
                    models.Family.name.like(f"%{enquiry}%"),
                    models.Family.internal_id.like(f"%{enquiry}%"),
                )
            )
            if enquiry
            else records
        )
        records = records.filter_by(action=action) if action else records
        records = records.filter_by(data_analysis=data_analysis) if data_analysis else records
        return records.order_by(models.Family.created_at.desc())

    def family(self, internal_id: str) -> models.Family:
        """Fetch a family by internal id from the database."""
        return self.Family.query.filter_by(internal_id=internal_id).first()

    def family_samples(self, family_id: str) -> List[models.FamilySample]:
        """Find the samples of a family."""
        return (
            self.FamilySample.query.join(models.FamilySample.family, models.FamilySample.sample)
            .filter(models.Family.internal_id == family_id)
            .all()
        )

    def get_cases_from_ticket(self, ticket: str) -> Query:
        return self.Family.query.filter(models.Family.tickets.contains(ticket))

    def get_customer_id_from_ticket(self, ticket: str) -> str:
        """Returns the customer related to given ticket"""
        return (
            self.Family.query.filter(models.Family.tickets.contains(ticket))
            .first()
            .customer.internal_id
        )

    def get_samples_from_ticket(self, ticket: str) -> List[models.Sample]:
        return (
            self.Sample.query.join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.tickets.contains(ticket))
            .all()
        )

    def get_samples_from_flowcell(self, flowcell_name: str) -> List[models.Sample]:
        flowcell = self.query(models.Flowcell).filter(models.Flowcell.name == flowcell_name).first()
        if flowcell:
            return flowcell.samples

    def get_latest_ticket_from_case(self, case_id: str) -> str:
        """Returns the ticket from the most recent sample in a case"""
        return self.family(case_id).latest_ticket

    def get_latest_flow_cell_on_case(self, family_id: str) -> models.Flowcell:
        """Fetch the latest sequenced flow cell related to a sample on a case"""
        case_obj: models.Family = self.family(family_id)
        samples_on_case = case_obj.links
        flow_cells_on_case: List[models.Flowcell] = samples_on_case[0].sample.flowcells
        flow_cells_on_case.sort(key=lambda flow_cell: flow_cell.sequenced_at)
        # .sort() sorts by ascending order by default
        return flow_cells_on_case[-1]

    def get_samples_by_family_id(self, family_id: str) -> List[models.Sample]:
        """Get samples on a given family_id."""

        case: models.Family = self.family(internal_id=family_id)
        return case.samples if case else []

    def get_sequenced_samples(self, family_id: str) -> List[models.Sample]:
        """Get sequenced samples by family_id."""

        samples: List[models.Sample] = self.get_samples_by_family_id(family_id)
        return [sample for sample in samples if sample.sequencing_qc]

    def find_family(self, customer: models.Customer, name: str) -> models.Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(customer=customer, name=name).first()

    def find_family_by_name(self, name: str) -> models.Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(name=name).first()

    def find_samples(self, customer: models.Customer, name: str) -> Query:
        """Find samples within a customer."""
        return self.Sample.query.filter_by(customer=customer, name=name)

    def get_flow_cell(self, flow_cell_id: str) -> Flowcell:
        """Return flow cell."""
        return apply_flow_cell_filter(
            flow_cells=self.Flowcell.query, flow_cell_id=flow_cell_id, function="flow_cell_has_id"
        )

    def flowcells(
        self, *, status: str = None, family: models.Family = None, enquiry: str = None
    ) -> Query:
        """Fetch all flowcells."""
        records = self.Flowcell.query
        if family:
            records = records.join(models.Flowcell.samples, models.Sample.links).filter(
                models.FamilySample.family == family
            )
        if status:
            records = records.filter_by(status=status)
        if enquiry:
            records = records.filter(models.Flowcell.name.like(f"%{enquiry}%"))
        return records.order_by(models.Flowcell.sequenced_at.desc())

    def invoices(self, invoiced: bool = None) -> Query:
        """Fetch invoices."""
        query = self.Invoice.query
        if invoiced:
            query = query.filter(models.Invoice.invoiced_at.isnot(None))
        else:
            query = query.filter(models.Invoice.invoiced_at.is_(None))
        return query

    def invoice(self, invoice_id: int) -> models.Invoice:
        """Fetch an invoice."""
        return self.Invoice.get(invoice_id)

    def invoice_samples(self, *, invoice_id: int = None) -> Query:
        """Fetch pools and samples for an invoice"""
        pools = self.Pool.query.filter_by(invoice_id=invoice_id).all()
        samples = self.Sample.query.filter_by(invoice_id=invoice_id).all()
        return pools + samples

    def link(self, family_id: str, sample_id: str) -> models.FamilySample:
        """Find a link between a family and a sample."""
        return (
            self.FamilySample.query.join(models.FamilySample.family, models.FamilySample.sample)
            .filter(models.Family.internal_id == family_id, models.Sample.internal_id == sample_id)
            .first()
        )

    def new_invoice_id(self) -> int:
        """Fetch invoices."""
        query = self.Invoice.query.all()
        ids = [inv.id for inv in query]
        return max(ids) + 1 if ids else 0

    def pools(
        self, *, customers: Optional[List[models.Customer]] = None, enquiry: str = None
    ) -> Query:
        """Fetch all the pools for a customer."""
        records = self.Pool.query

        if customers:
            customer_ids = []
            for customer in customers:
                customer_ids.append(customer.id)
            records = records.filter(models.Pool.customer_id.in_(customer_ids))

        records = (
            records.filter(
                or_(models.Pool.name.like(f"%{enquiry}%"), models.Pool.order.like(f"%{enquiry}%"))
            )
            if enquiry
            else records
        )

        return records.order_by(models.Pool.created_at.desc())

    def pool(self, pool_id: int) -> models.Pool:
        """Fetch a pool."""
        return self.Pool.get(pool_id)

    def get_ready_made_library_expected_reads(self, case_id: str) -> int:
        """Return the target reads of a ready made library case."""

        application: models.Application = self.get_application_by_case(case_id)

        if application.prep_category != PrepCategory.READY_MADE_LIBRARY.value:

            raise ValueError(
                f"{case_id} is not a ready made library, found prep category: "
                f"{application.prep_category}"
            )
        return application.expected_reads

    def sample(self, internal_id: str) -> models.Sample:
        """Fetch a sample by lims id."""
        return self.Sample.query.filter_by(internal_id=internal_id).first()

    def samples(
        self, *, customers: Optional[List[models.Customer]] = None, enquiry: str = None
    ) -> Query:
        records = self.Sample.query

        if customers:
            customer_ids = []
            for customer in customers:
                customer_ids.append(customer.id)
            records = records.filter(models.Sample.customer_id.in_(customer_ids))

        records = (
            records.filter(
                or_(
                    models.Sample.name.like(f"%{enquiry}%"),
                    models.Sample.internal_id.like(f"%{enquiry}%"),
                )
            )
            if enquiry
            else records
        )
        return records.order_by(models.Sample.created_at.desc())

    def samples_by_subject_id(
        self, customer_id: str, subject_id: str, is_tumour: bool = None
    ) -> Query:
        """Get samples of customer with given subject_id.

        Args:
            customer_id  (str):               Internal-id of customer
            subject_id   (str):               Subject id
            is_tumour    (bool):              (Optional) match on is_tumour
        Returns:
            matching samples (list of models.Sample)
        """

        query: Query = self.Sample.query.join(models.Customer).filter(
            models.Customer.internal_id == customer_id, models.Sample.subject_id == subject_id
        )
        if is_tumour:
            query: Query = query.filter(models.Sample.is_tumour == is_tumour)
        return query

    def samples_by_ids(self, **identifiers) -> Query:
        records = self.Sample.query

        for identifier_name, identifier_value in identifiers.items():
            identifier = getattr(models.Sample, identifier_name)
            records = records.filter(identifier.contains(identifier_value))

        return records.order_by(models.Sample.internal_id.desc())

    def get_sample_by_name(self, name: str) -> models.Sample:
        return self.Sample.query.filter(models.Sample.name == name).first()

    def get_case_pool(self, case_id: str) -> Optional[models.Pool]:
        """Returns the pool connected to the case. Returns None if no pool is found"""
        case: models.Family = self.family(internal_id=case_id)
        pool_name: str = case.name.split("-", 1)[-1]
        return self.pools(customers=[case.customer], enquiry=pool_name).first()

    def is_pool(self, case_id: str) -> bool:
        return bool(self.get_case_pool(case_id=case_id))
