"""Handler to find basic data objects"""
import datetime as dt
from typing import List, Optional, Callable

from sqlalchemy import desc
from sqlalchemy.orm import Query

from cg.store.models import (
    Application,
    ApplicationVersion,
    Bed,
    BedVersion,
    Customer,
    Collaboration,
    Organism,
    Panel,
    User,
)
from cg.store.api.base import BaseHandler
from cg.store.status_bed_filters import apply_bed_filter, BedFilters
from cg.store.status_bed_version_filters import BedVersionFilters, apply_bed_version_filter
from cg.store.status_collaboration_filters import (
    CollaborationFilters,
    apply_collaboration_filter,
)


class FindBasicDataHandler(BaseHandler):
    """Contains methods to find basic data model instances"""

    def application(self, tag: str) -> Application:
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

    def application_version(self, application: Application, version: int) -> ApplicationVersion:
        """Fetch an application version."""
        query = self.ApplicationVersion.query.filter_by(application=application, version=version)
        return query.first()

    def get_bed_version_by_short_name(self, bed_version_short_name: str) -> BedVersion:
        """Return bed version with short name."""
        return apply_bed_version_filter(
            bed_versions=self._get_query(table=BedVersion),
            bed_version_short_name=bed_version_short_name,
            functions=[BedVersionFilters.get_bed_version_by_short_name],
        ).first()

    def get_bed_by_name(self, bed_name: str) -> Optional[Bed]:
        """Return bed by name."""
        return apply_bed_filter(
            beds=self._get_query(table=Bed),
            bed_name=bed_name,
            functions=[BedFilters.get_beds_by_name],
        ).first()

    def get_active_beds(self) -> Query:
        """Get all beds which are not archived."""
        bed_filter_functions: List[Callable] = [
            BedFilters.get_not_archived_beds,
            BedFilters.order_beds_by_name,
        ]
        return apply_bed_filter(beds=self._get_query(table=Bed), functions=bed_filter_functions)

    def get_latest_bed_version(self, bed_name: str) -> Optional[BedVersion]:
        """Return the latest bed version for a bed by supplied name."""
        bed: Optional[Bed] = self.get_bed_by_name(bed_name=bed_name)
        return bed.versions[-1] if bed and bed.versions else None

    def customer(self, internal_id: str) -> Customer:
        """Fetch a customer by internal id from the store."""
        return self.Customer.query.filter_by(internal_id=internal_id).first()

    def customers(self) -> List[Customer]:
        """Fetch all customers."""
        return self.Customer.query

    def get_collaboration_by_internal_id(self, internal_id: str) -> Collaboration:
        """Fetch a customer group by internal id from the store."""
        return apply_collaboration_filter(
            collaborations=self._get_query(table=Collaboration),
            filter_functions=[CollaborationFilters.FILTER_BY_INTERNAL_ID],
            internal_id=internal_id,
        ).first()

    def customer_by_id(self, id_: int) -> Customer:
        """Fetch a customer by id number from the store."""
        return self.Customer.query.filter_by(id=id_).first()

    def current_application_version(self, tag: str) -> Optional[ApplicationVersion]:
        """Fetch the current application version for an application tag."""
        application_obj = self.Application.query.filter_by(tag=tag).first()
        if not application_obj:
            return None
        application_id = application_obj.id
        records = self.ApplicationVersion.query.filter_by(application_id=application_id)
        records = records.filter(self.ApplicationVersion.valid_from < dt.datetime.now())
        records = records.order_by(desc(self.ApplicationVersion.valid_from))

        return records.first()

    def latest_version(self, tag: str) -> Optional[ApplicationVersion]:
        """Fetch the latest application version for an application tag."""
        application_obj = self.Application.query.filter_by(tag=tag).first()
        return (
            application_obj.versions[-1] if application_obj and application_obj.versions else None
        )

    def organism(self, internal_id: str) -> Organism:
        """Find an Organism by internal_id."""
        return self.Organism.query.filter_by(internal_id=internal_id).first()

    def organisms(self) -> List[Organism]:
        """Fetch all organisms"""
        return self.Organism.query.order_by(Organism.internal_id)

    def panel(self, abbrev):
        """Find a panel by abbreviation."""
        return self.Panel.query.filter_by(abbrev=abbrev).first()

    def panels(self):
        """Returns all panels."""
        return self.Panel.query.order_by(Panel.abbrev)

    def user(self, email: str) -> User:
        """Fetch a user from the store."""
        return self.User.query.filter_by(email=email).first()
