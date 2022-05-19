"""Handler to find business data objects"""
import datetime as dt
import logging
from typing import List, Optional, Set

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query
from cg.store import models
from cg.store.api.base import BaseHandler
from cgmodels.cg.constants import Pipeline


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
        self, *, customers: [models.Customer] = None, enquiry: str = None, action: str = None
    ) -> Query:
        """Fetch families."""

        records = self.Family.query

        if customers:
            customer_ids = []
            for customer in customers:
                customer_ids.append(customer.id)
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
        return records.order_by(models.Family.created_at.desc())

    def families_in_customer_group(
        self, *, customers: List[models.Customer] = None, enquiry: str = None
    ) -> Query:
        """Fetch all families including those from collaborating customers."""
        records = self.Family.query.join(models.Family.customer, models.Customer.customer_group)

        if customers:
            customer_group_ids = []
            for customer in customers:
                customer_group_ids.append(customer.customer_group_id)
            records = records.filter(models.CustomerGroup.id.in_(customer_group_ids))

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

    def families_by_subject_id(
        self,
        customer_id: str,
        subject_id: str,
        data_analyses: [Pipeline] = None,
        is_tumour: bool = None,
    ) -> Set[models.Family]:
        """Get all cases that have a sample for a subject_id.

        Args:
            customer_id     (str):                 Customer-id of customer owning the cases
            subject_id      (str):                 Subject-id to search for
            data_analyses   (list[Pipeline]):      Optional list of data_analysis values to filter on
            is_tumour       (bool):                Optional is_tumour value to filter on
        Returns:
            set containing the matching cases set(models.Family)
        """
        cases: set[models.Family] = set()
        samples: [models.Sample] = self.samples_by_subject_id(
            customer_id=customer_id, subject_id=subject_id, is_tumour=is_tumour
        )
        sample: models.Sample
        for sample in samples:
            link: models.FamilySample
            for link in sample.links:
                case: models.Family = link.family

                if data_analyses and case.data_analysis not in data_analyses:
                    continue

                cases.add(case)
        return cases

    def get_cases_from_ticket(self, ticket_id: int) -> Query:
        return self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.ticket_number == ticket_id
        )

    def get_customer_id_from_ticket(self, ticket_id: int) -> str:
        """Returns the customer related to given ticket"""
        return (
            self.Sample.query.filter(models.Sample.ticket_number == ticket_id)
            .first()
            .customer.internal_id
        )

    def get_samples_from_ticket(self, ticket_id: int) -> List[models.Sample]:
        return self.query(models.Sample).filter(models.Sample.ticket_number == ticket_id).all()

    def get_samples_from_flowcell(self, flowcell_name: str) -> List[models.Sample]:
        flowcell = self.query(models.Flowcell).filter(models.Flowcell.name == flowcell_name).first()
        if flowcell:
            return flowcell.samples

    def get_ticket_from_case(self, case_id: str) -> int:
        """Returns the ticket from the most recent sample in a case"""
        newest_sample: models.Sample = (
            self.Sample.query.join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.internal_id == case_id)
            .order_by(models.Sample.created_at.desc())
            .first()
        )
        return newest_sample.ticket_number

    def get_latest_flow_cell_on_case(self, family_id: str) -> models.Flowcell:
        """Fetch the latest sequenced flow cell related to a sample on a case"""
        case_obj: models.Family = self.family(family_id)
        samples_on_case = case_obj.links
        flow_cells_on_case: List[models.Flowcell] = samples_on_case[0].sample.flowcells
        flow_cells_on_case.sort(key=lambda flow_cell: flow_cell.sequenced_at)
        # .sort() sorts by ascending order by default
        return flow_cells_on_case[-1]

    def get_samples_by_family_id(self, family_id: str) -> List[models.Sample]:
        """Get samples on a given family_id"""
        case: models.Family = self.family(internal_id=family_id)
        return [link.sample for link in case.links] if case else []

    def get_sequenced_samples(self, family_id: str) -> List[models.Sample]:
        """Get sequenced samples by family_id"""

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

    def flowcell(self, name: str) -> models.Flowcell:
        """Fetch a flowcell."""
        return self.Flowcell.query.filter(models.Flowcell.name == name).first()

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

    def links(self, case_id: str, sample_id: str, ticket: int) -> Query:
        """Find a link between a family and a sample."""

        query = self.FamilySample.query.join(models.FamilySample.family, models.FamilySample.sample)

        if case_id:
            query = query.filter(models.Family.internal_id == case_id)

        if sample_id:
            query = query.filter(models.Sample.internal_id == sample_id)

        if ticket:
            query = query.filter(models.Sample.ticket_number == ticket)

        return query

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
        if is_tumour is not None:
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

    def samples_in_customer_group(
        self, *, customers: Optional[List[models.Customer]] = None, enquiry: str = None
    ) -> Query:
        """Fetch all samples including those from collaborating customers."""

        records = self.Sample.query.join(models.Sample.customer, models.Customer.customer_group)

        if customers:
            customer_group_ids = []
            for customer in customers:
                customer_group_ids.append(customer.customer_group_id)
            records = records.filter(models.CustomerGroup.id.in_(customer_group_ids))

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

    def get_case_pool(self, case_id: str) -> Optional[models.Pool]:
        """Returns the pool connected to the case. Returns None if no pool is found"""
        case: models.Family = self.family(internal_id=case_id)
        pool_name: str = case.name.split("-", 1)[-1]
        return self.pools(customers=[case.customer], enquiry=pool_name).first()

    def is_pool(self, case_id: str) -> bool:
        return bool(self.get_case_pool(case_id=case_id))
