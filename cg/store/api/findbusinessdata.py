"""Handler to find business data objects"""
import datetime as dt
from typing import List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query

from cg.store import models
from cg.store.api.base import BaseHandler


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

    def find_family_by_avatar_url(self, avatar_url: str) -> models.Family:
        """Fetch a family by avatar_url from the database."""
        return self.Family.query.filter_by(avatar_url=avatar_url).first()

    def find_family_by_name(self, name: str) -> models.Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(name=name).first()

    def find_sample(self, customer: models.Customer, name: str) -> Query:
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

    def samples_by_ids(self, **identifiers) -> Query:
        records = self.Sample.query

        for identifier_name, identifier_value in identifiers.items():
            identifier = getattr(models.Sample, identifier_name)
            records = records.filter(identifier.contains(identifier_value))

        return records.order_by(models.Sample.internal_id.desc())

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
