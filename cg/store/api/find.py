# -*- coding: utf-8 -*-
import datetime as dt
from typing import List

from cg.store import models


class FindHandler:

    def customer(self, internal_id: str) -> models.Customer:
        """Fetch a customer by internal id from the store."""
        return self.Customer.query.filter_by(internal_id=internal_id).first()

    def user(self, email: str) -> models.User:
        """Fetch a user from the store."""
        return self.User.query.filter_by(email=email).first()

    def family(self, internal_id: str) -> models.Family:
        """Fetch a family by internal id from the database."""
        return self.Family.query.filter_by(internal_id=internal_id).first()

    def families(self, *, customer: models.Customer=None, query: str=None) -> List[models.Family]:
        """Fetch all families."""
        records = self.Family.query
        records = records.filter_by(customer=customer) if customer else records
        records = records.filter(models.Family.name.like(f"%{query}%")) if query else records
        return records.order_by(models.Family.created_at.desc())

    def find_family(self, customer: models.Customer, name: str) -> models.Family:
        """Find a family by family name within a customer."""
        return self.Family.query.filter_by(customer=customer, name=name).first()

    def sample(self, internal_id: str) -> models.Sample:
        """Fetch a sample by lims id."""
        return self.Sample.query.filter_by(internal_id=internal_id).first()

    def samples(self, *, customer: models.Customer=None, query: str=None) -> List[models.Sample]:
        records = self.Sample.query
        records = records.filter_by(customer=customer) if customer else records
        records = records.filter(models.Sample.name.like(f"%{query}%")) if query else records
        return records.order_by(models.Sample.created_at.desc())

    def find_sample(self, customer: models.Customer, name: str) -> models.Sample:
        """Find a sample within a customer."""
        return self.Sample.query.filter_by(customer=customer, name=name).first()

    def application(self, tag: str) -> models.Application:
        """Fetch an application from the store."""
        return self.Application.query.filter_by(tag=tag).first()

    def application_version(self, application: models.Application,
                            version: int) -> models.ApplicationVersion:
        """Fetch an application version."""
        query = self.ApplicationVersion.query.filter_by(application=application, version=version)
        return query.first()

    def panel(self, abbrev):
        """Find a panel by abbreviation."""
        return self.Panel.query.filter_by(abbrev=abbrev).first()

    def analysis(self, family: models.Family, analyzed: dt.datetime) -> models.Analysis:
        """Fetch an analysis."""
        return self.Analysis.query.filter_by(family=family, analyzed_at=analyzed).first()
