# -*- coding: utf-8 -*-
import datetime as dt
from typing import List

from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Query

from cg.store.api.base import BaseHandler
from cg.store import models


class FindHandler(BaseHandler):
    """Contains methods to find model instances"""

    def customer(self, internal_id: str) -> models.Customer:
        """Fetch a customer by internal id from the store."""
        return self.Customer.query.filter_by(internal_id=internal_id).first()

    def customers(self) -> List[models.Customer]:
        """Fetch all customers."""
        return self.Customer.query

    def customer_group(self, internal_id: str) -> models.CustomerGroup:
        """Fetch a customer group by internal id from the store."""
        return self.CustomerGroup.query.filter_by(internal_id=internal_id).first()

    def customer_by_id(self, id_: int) -> models.Customer:
        """Fetch a customer by id number from the store."""
        return self.Customer.query.filter_by(id=id_).first()

    def user(self, email: str) -> models.User:
        """Fetch a user from the store."""
        return self.User.query.filter_by(email=email).first()

    def family(self, internal_id: str) -> models.Family:
        """Fetch a family by internal id from the database."""
        return self.Family.query.filter_by(internal_id=internal_id).first()

    def families(self, *, customer: models.Customer = None, enquiry: str = None,
                 action: str = None) -> List[models.Family]:
        """Fetch families."""
        records = self.Family.query
        records = records.filter_by(customer=customer) if customer else records

        records = records.filter(or_(
            models.Family.name.like(f"%{enquiry}%"),
            models.Family.internal_id.like(f"%{enquiry}%"),
        )) if enquiry else records

        records = records.filter_by(action=action) if action else records

        return records.order_by(models.Family.created_at.desc())

    def families_in_customer_group(self, *, customer: models.Customer = None, enquiry: str =
    None) -> List[models.Family]:
        """Fetch all families including those from collaborating customers."""
        records = self.Family.query \
            .join(
            models.Family.customer,
            models.Customer.customer_group,
        )

        if customer:
            records = records.filter(
                models.CustomerGroup.id == customer.customer_group_id)

        records = records.filter(or_(
            models.Family.name.like(f"%{enquiry}%"),
            models.Family.internal_id.like(f"%{enquiry}%"),
        )) if enquiry else records

        return records.order_by(models.Family.created_at.desc())

    def find_family(self, customer: models.Customer, name: str) -> models.Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(customer=customer, name=name).first()

    def sample(self, internal_id: str) -> models.Sample:
        """Fetch a sample by lims id."""
        return self.Sample.query.filter_by(internal_id=internal_id).first()

    def samples(self, *, customer: models.Customer = None, enquiry: str = None) -> List[
        models.Sample]:
        records = self.Sample.query
        records = records.filter_by(customer=customer) if customer else records
        records = records.filter(or_(
            models.Sample.name.like(f"%{enquiry}%"),
            models.Sample.internal_id.like(f"%{enquiry}%"),
        )) if enquiry else records
        return records.order_by(models.Sample.created_at.desc())

    def samples_in_customer_group(self, *, customer: models.Customer = None, enquiry: str = None)\
            -> List[models.Sample]:
        """Fetch all samples including those from collaborating customers."""

        records = self.Sample.query \
            .join(
            models.Sample.customer,
            models.Customer.customer_group,
        )

        if customer:
            records = records.filter(
                models.CustomerGroup.id == customer.customer_group_id)

        records = records.filter(or_(
            models.Sample.name.like(f"%{enquiry}%"),
            models.Sample.internal_id.like(f"%{enquiry}%"),
        )) if enquiry else records
        return records.order_by(models.Sample.created_at.desc())

    def microbial_samples(self, *, customer: models.Customer = None, enquiry: str = None) -> List[
        models.MicrobialSample]:
        records = self.MicrobialSample.query
        records = records.filter_by(customer=customer) if customer else records
        records = records.filter(or_(
            models.MicrobialSample.name.like(f"%{enquiry}%"),
            models.MicrobialSample.internal_id.like(f"%{enquiry}%"),
        )) if enquiry else records
        return records.order_by(models.MicrobialSample.created_at.desc())

    def microbial_sample(self, internal_id: str) -> models.MicrobialSample:
        """Fetch a microbial sample by lims id."""
        return self.MicrobialSample.query.filter_by(internal_id=internal_id).first()

    def find_sample(self, customer: models.Customer, name: str) -> List[models.Sample]:
        """Find samples within a customer."""
        return self.Sample.query.filter_by(customer=customer, name=name)

    def find_sample_in_customer_group(self, customer: models.Customer, name: str) -> List[
        models.Sample]:
        """Find samples within the customer group."""
        return self.Sample.query.filter(
            models.Sample.customer.customer_group == customer.customer_group, name == name)

    def application(self, tag: str) -> models.Application:
        """Fetch an application from the store."""
        return self.Application.query.filter_by(tag=tag).first()

    def applications(self, *, category=None, archived=None):
        """Fetch all applications."""
        records = self.Application.query
        if category:
            records = records.filter_by(prep_category=category)
        if archived is not None:
            records = records.filter_by(is_archived=archived)
        return records

    def application_version(self, application: models.Application,
                            version: int) -> models.ApplicationVersion:
        """Fetch an application version."""
        query = self.ApplicationVersion.query.filter_by(application=application, version=version)
        return query.first()

    def latest_version(self, tag: str) -> models.ApplicationVersion:
        """Fetch the latest application version for an application tag."""
        application_obj = self.Application.query.filter_by(tag=tag).first()
        return application_obj.versions[-1] if application_obj and application_obj.versions else \
            None
