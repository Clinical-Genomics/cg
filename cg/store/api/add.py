# -*- coding: utf-8 -*-
import logging
import datetime as dt
from typing import List

import petname

from cg.constants import PRIORITY_MAP
from cg.exc import MissingCustomerError, DuplicateRecordError
from cg.store import models, utils

log = logging.getLogger(__name__)


class AddHandler:

    def add_customer(self, internal_id: str, name: str, scout: bool=False) -> models.Customer:
        """Add a new customer to the database."""
        new_customer = self.Customer(internal_id=internal_id, name=name, scout_access=scout)
        return new_customer

    def add_user(self, email: str, name: str, admin: bool=False) -> models.User:
        """Add a new user to the database."""
        new_user = self.User(name=name, email=email, is_admin=admin)
        return new_user

    def add_application(self, tag: str, category: str, description: str,
                        accredited: bool=False) -> models.Application:
        """Add a new application to the store."""
        new_record = self.Application(
            tag=tag,
            category=category,
            description=description,
            is_accredited=accredited
        )
        return new_record

    def add_version(self, version: int, valid: dt.datetime, prices: dict,
                    comment: str=None) -> models.ApplicationVersion:
        """Add application version."""
        new_record = self.ApplicationVersion(version=version, valid_from=valid, comment=comment)
        for price_key in ['standard', 'priority', 'express', 'research']:
            setattr(new_record, f"price_{price_key}", prices[price_key])
        return new_record

    def add_sample(self, name: str, sex: str, internal_id: str=None, received: dt.datetime=None,
                   order: str=None, external: bool=False, tumour: bool=False) -> models.Sample:
        """Add a new sample to the database."""
        internal_id = internal_id or utils.get_unique_id(self.sample)
        new_sample = self.Sample(name=name, internal_id=internal_id, received_at=received,
                                 sex=sex, order=order, is_external=external, is_tumour=tumour)
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

    def add_flowcell(self, name: str, sequencer: str, sequenced: dt.datetime) -> models.Flowcell:
        new_record = self.Flowcell(name=name, sequencer_type=sequencer, sequenced_at=sequenced)
        return new_record

    def add_analysis(self, pipeline: str, version: str, analyzed: dt.datetime,
                     primary: bool=False) -> models.Analysis:
        """Add a new analysis to the database."""
        new_record = self.Analysis(pipeline=pipeline, pipeline_version=version,
                                   analyzed_at=analyzed, is_primary=primary)
        return new_record

    def add_panel(self, name: str, abbrev: str, version: float, date: dt.datetime=None,
                  genes: int=None) -> models.Panel:
        """Build a new panel."""
        new_record = self.Panel(name=name, abbrev=abbrev, current_version=version, date=date,
                                gene_count=genes)
        return new_record

    def add_order(self, data: dict) -> List[models.Family]:
        """Add a new order of samples to the database."""
        customer_obj = self.customer(data['customer'])
        if customer_obj is None:
            raise MissingCustomerError(f"can't find customer: {data['customer']}")
        records = []
        for family in data['families']:
            existing_record = self.find_family(customer_obj, family['name'])
            if existing_record:
                raise DuplicateRecordError(f"existing family found: {existing_record.name} "
                                           f"({existing_record.internal_id})")

            family_obj = self.add_family(
                name=family['name'],
                panels=family['panels'],
                priority=family['priority'],
            )
            family_obj.customer = customer_obj
            self.add(family_obj)

            family_samples = {}
            for sample in family['samples']:
                existing_record = self.find_sample(customer_obj, sample['name'])
                if existing_record:
                    raise DuplicateRecordError(f"existing sample found: {existing_record.name} "
                                               f"({existing_record.internal_id})")
                sample_obj = self.add_sample(
                    name=sample['name'],
                    sex=sample['sex'],
                    internal_id=sample['internal_id'],
                    order=data['name'],
                )
                application_obj = self.application(sample['application'])
                sample_obj.application_version = application_obj.versions[-1]
                sample_obj.customer = customer_obj
                family_samples[sample_obj.name] = sample_obj
                self.add(sample_obj)

            for sample in family['samples']:
                relationship_obj = self.relate_sample(
                    family=family_obj,
                    sample=family_samples[sample['name']],
                    status=sample['status'],
                    mother=family_samples[sample['mother']] if sample.get('mother') else None,
                    father=family_samples[sample['father']] if sample.get('father') else None,
                )
                self.add(relationship_obj)

            records.append(family_obj)
        return records
