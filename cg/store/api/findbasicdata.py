"""Handler to find basic data objects"""
import datetime as dt
from typing import List

from sqlalchemy import desc

from cg.store.api.base import BaseHandler
from cg.store import models


class FindBasicDataHandler(BaseHandler):
    """Contains methods to find basic data model instances"""

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
        return records.order_by(self.Application.prep_category, self.Application.tag)

    def application_version(
        self, application: models.Application, version: int
    ) -> models.ApplicationVersion:
        """Fetch an application version."""
        query = self.ApplicationVersion.query.filter_by(application=application, version=version)
        return query.first()

    def bed(self, name):
        """Find a bed by name."""
        return self.Bed.query.filter_by(name=name).first()

    def bed_version(self, shortname):
        """Find a bed version by shortname."""
        return self.BedVersion.query.filter_by(shortname=shortname).first()

    def beds(self, hide_archived: bool = False):
        """Returns all beds."""
        bed_q = self.Bed.query
        if hide_archived:
            bed_q = bed_q.filter(self.Bed.is_archived.is_(False))

        return bed_q.order_by(models.Bed.name)

    def latest_bed_version(self, name: str) -> models.BedVersion:
        """Fetch the latest bed version for a bed name."""
        bed_obj = self.Bed.query.filter_by(name=name).first()
        return bed_obj.versions[-1] if bed_obj and bed_obj.versions else None

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

    def current_application_version(self, tag: str) -> models.ApplicationVersion:
        """Fetch the current application version for an application tag."""
        application_obj = self.Application.query.filter_by(tag=tag).first()
        if not application_obj:
            return None
        application_id = application_obj.id
        records = self.ApplicationVersion.query.filter_by(application_id=application_id)
        records = records.filter(self.ApplicationVersion.valid_from < dt.datetime.now())
        records = records.order_by(desc(self.ApplicationVersion.valid_from))

        return records.first()

    def latest_version(self, tag: str) -> models.ApplicationVersion:
        """Fetch the latest application version for an application tag."""
        application_obj = self.Application.query.filter_by(tag=tag).first()
        return (
            application_obj.versions[-1] if application_obj and application_obj.versions else None
        )

    def organism(self, internal_id: str) -> models.Organism:
        """Find an Organism by internal_id."""
        return self.Organism.query.filter_by(internal_id=internal_id).first()

    def organisms(self) -> List[models.Organism]:
        """Fetch all organisms"""
        return self.Organism.query.order_by(models.Organism.internal_id)

    def panel(self, abbrev):
        """Find a panel by abbreviation."""
        return self.Panel.query.filter_by(abbrev=abbrev).first()

    def panels(self):
        """Returns all panels."""
        return self.Panel.query.order_by(models.Panel.abbrev)

    def user(self, email: str) -> models.User:
        """Fetch a user from the store."""
        return self.User.query.filter_by(email=email).first()
