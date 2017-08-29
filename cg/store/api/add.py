# -*- coding: utf-8 -*-
import logging
import datetime as dt
from typing import List

import petname

from cg.constants import PRIORITY_MAP
from cg.store import models, utils

log = logging.getLogger(__name__)


class AddHandler:

    def add_customer(self, internal_id: str, name: str, scout_access: bool=False,
                     **kwargs) -> models.Customer:
        """Add a new customer to the database."""
        new_customer = self.Customer(internal_id=internal_id, name=name, scout_access=scout_access,
                                     **kwargs)
        return new_customer

    def add_user(self, customer: models.Customer, email: str, name: str,
                 is_admin: bool=False) -> models.User:
        """Add a new user to the database."""
        new_user = self.User(name=name, email=email, is_admin=is_admin)
        new_user.customer = customer
        return new_user

    def add_application(self, tag: str, category: str, description: str,
                        is_accredited: bool=False, **kwargs) -> models.Application:
        """Add a new application to the store."""
        new_record = self.Application(
            tag=tag,
            category=category,
            description=description,
            is_accredited=is_accredited,
            **kwargs,
        )
        return new_record

    def add_version(self, application: models.Application, version: int, valid_from: dt.datetime,
                    prices: dict, **kwargs) -> models.ApplicationVersion:
        """Add application version."""
        new_record = self.ApplicationVersion(version=version, valid_from=valid_from, **kwargs)
        for price_key in ['standard', 'priority', 'express', 'research']:
            setattr(new_record, f"price_{price_key}", prices[price_key])
        new_record.application = application
        return new_record

    def add_sample(self, name: str, sex: str, internal_id: str=None, ordered: dt.datetime=None,
                   received: dt.datetime=None, order: str=None, external: bool=False,
                   tumour: bool=False, priority: str='standard', ticket: int=None,
                   comment: str=None, **kwargs) -> models.Sample:
        """Add a new sample to the database."""
        internal_id = internal_id or utils.get_unique_id(self.sample)
        db_priority = PRIORITY_MAP[priority]
        new_sample = self.Sample(name=name, internal_id=internal_id, received_at=received,
                                 sex=sex, order=order, is_external=external, is_tumour=tumour,
                                 ordered_at=ordered or dt.datetime.now(), priority=db_priority,
                                 ticket_number=ticket, comment=comment, **kwargs)
        return new_sample

    def add_family(self, name: str, panels: List[str], priority: str='standard') -> models.Family:
        """Add a new family to the database."""
        # generate a unique family id
        while True:
            internal_id = petname.Generate(2, separator='')
            if self.family(internal_id) is None:
                break
            else:
                log.debug(f"{internal_id} already used - trying another id")

        db_priority = PRIORITY_MAP[priority]
        new_family = self.Family(internal_id=internal_id, name=name, priority=db_priority)
        new_family.panels = panels
        return new_family

    def relate_sample(self, family: models.Family, sample: models.Sample,
                      status: str, mother: models.Sample=None,
                      father: models.Sample=None) -> models.FamilySample:
        """Relate a sample to a family."""
        new_record = self.FamilySample(status=status)
        new_record.family = family
        new_record.sample = sample
        new_record.mother = mother
        new_record.father = father
        return new_record

    def add_flowcell(self, name: str, sequencer: str, sequencer_type: str,
                     date: dt.datetime) -> models.Flowcell:
        new_record = self.Flowcell(name=name, sequencer_name=sequencer,
                                   sequencer_type=sequencer_type, sequenced_at=date)
        return new_record

    def add_analysis(self, pipeline: str, version: str, completed_at: dt.datetime,
                     primary: bool=False, uploaded: dt.datetime=None) -> models.Analysis:
        """Add a new analysis to the database."""
        new_record = self.Analysis(pipeline=pipeline, pipeline_version=version,
                                   completed_at=completed_at, is_primary=primary, uploaded_at=uploaded)
        return new_record

    def add_panel(self, customer: models.Customer, name: str, abbrev: str, version: float,
                  date: dt.datetime=None, genes: int=None) -> models.Panel:
        """Build a new panel."""
        new_record = self.Panel(name=name, abbrev=abbrev, current_version=version, date=date,
                                gene_count=genes)
        new_record.customer = customer
        return new_record

    def add_pool(self, customer: models.Customer, name: str, order: str, ordered: dt.datetime,
                 application_version: models.ApplicationVersion, ticket: int=None,
                 comment: str=None, received: dt.datetime=None) -> models.Pool:
        """Build a new Pool record."""
        new_record = self.Pool(name=name, ordered_at=ordered, order=order,
                               ticket_number=ticket, received_at=received, comment=comment)
        new_record.customer = customer
        new_record.application_version = application_version
        return new_record

    def add_delivery(self, destination: str, sample: models.Sample=None, pool: models.Pool=None,
                     comment: str=None) -> models.Delivery:
        """Build a new Delivery record."""
        if not any([sample, pool]):
            raise ValueError('you have to provide a sample or a pool')
        new_record = self.Delivery(destination=destination, comment=comment)
        new_record.sample = sample
        new_record.pool = pool
        return new_record
