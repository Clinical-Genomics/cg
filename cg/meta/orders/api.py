# -*- coding: utf-8 -*-
import datetime as dt
from enum import Enum
from typing import List

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.exc import OrderError
from cg.store import Store, models
from .schema import ExternalProject, FastqProject, RmlProject, ScoutProject


class OrderType(Enum):
    EXTERNAL = 'external'
    FASTQ = 'fastq'
    RML = 'rml'
    SCOUT = 'scout'


class OrdersAPI():

    types = {
        OrderType.EXTERNAL: ExternalProject(),
        OrderType.FASTQ: FastqProject(),
        OrderType.RML: RmlProject(),
        OrderType.SCOUT: ScoutProject()
    }

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket):
        self.lims = lims
        self.status = status
        self.osticket = osticket

    def submit(self, type: OrderType, name: str, email: str, data: dict) -> dict:
        """Submit a batch of samples."""
        errors = self.types[type].validate(data)
        if errors:
            return errors
        message = f"New incoming samples, {name}"
        data['ticket'] = (self.osticket.open_ticket(name, email, subject=data['name'],
                                                    message=message)
                          if self.osticket else None)
        result = getattr(self, f"submit_{type.value}")(data)
        self.status.commit()
        return result

    def submit_rml(self, data: dict) -> dict:
        """Submit a batch of ready made libraries."""
        status_data = self.pools_to_status(data)
        project_data, _ = self.process_lims(data)
        new_records = self.store_pools(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            pools=status_data['pools'],
        )
        return {'project': project_data, 'records': new_records}

    def submit_fastq(self, data: dict) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        status_data = self.samples_to_status(data)
        project_data, lims_map = self.process_lims(data)
        self.fillin_sample_ids(status_data['samples'], lims_map)
        new_records = self.store_samples(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            samples=status_data['samples'],
        )
        return {'project': project_data, 'records': new_records}

    def submit_external(self, data: dict) -> dict:
        """Submit a batch of externally sequenced samples for analysis."""
        result = self.process_analysis_samples(data)
        return result

    def submit_scout(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self.process_analysis_samples(data)
        return result

    def process_analysis_samples(self, data: dict) -> dict:
        """Process samples to be analyzed."""
        status_data = self.families_to_status(data)
        customer_obj = self.status.customer(status_data['customer'])
        for family in status_data['families']:
            family_obj = self.status.find_family(customer_obj, family['name'])
            if family_obj:
                raise OrderError(f"family name already used: {family_obj.name}")

        project_data, lims_map = self.process_lims(data)
        samples = [sample
                   for family in status_data['families']
                   for sample in family['samples']]
        self.fillin_sample_ids(samples, lims_map)
        new_families = self.store_families(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            families=status_data['families'],
        )
        return {'project': project_data, 'records': new_families}

    def process_lims(self, data: dict):
        lims_data = self.to_lims(data)
        project_data = self.lims.add_project(lims_data)
        lims_map = self.lims.get_samples(projectlimsid=project_data['id'], map_ids=True)
        return project_data, lims_map

    def fillin_sample_ids(self, samples: List[dict], lims_map: dict):
        """Fill in LIMS sample ids."""
        for sample in samples:
            sample['internal_id'] = lims_map.get(sample['name']) or sample['internal_id']

    @staticmethod
    def to_lims(data: dict) -> dict:
        """Convert order input to lims interface input."""
        lims_data = {
            'name': data['name'],
            'samples': [],
        }
        for sample in data['samples']:
            lims_data['samples'].append({
                'name': sample['name'],
                'container': sample.get('container') or 'Tube',
                'container_name': sample.get('container_name'),
                'well_position': sample.get('well_position'),
                'udfs': {
                    'family_name': sample.get('family_name') or 'NA',
                    'priority': sample.get('priority') or 'standard',
                    'application': sample['application'],
                    'require_qcok': sample.get('require_qcok') or False,
                    'quantity': sample.get('quantity'),
                    'volume': data.get('volume'),
                    'concentration': data.get('concentration'),
                    'source': sample.get('source') or 'NA',
                    'customer': data['customer'],
                    'comment': data.get('comment'),
                    'tumour': data.get('tumour'),
                    'pool': data.get('pool'),
                    'index': data.get('index'),
                    'index_number': data.get('index_number'),
                }
            })
        return lims_data

    @staticmethod
    def pools_to_status(data: dict) -> dict:
        """Convert input to pools."""
        pools = {}
        for sample in data['samples']:
            if sample['pool'] not in pools:
                pools[sample['pool']] = set()
            pools[sample['pool']].add(sample['application'])
        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'pools': []
        }
        for pool_name, applications in pools.items():
            if len(applications) != 1:
                raise OrderError(f"different application in pool: {pool_name} - {applications}")
            status_data['pools'].append({
                'name': pool_name,
                'application': applications.pop(),
            })
        return status_data

    @staticmethod
    def samples_to_status(data: dict) -> dict:
        """Convert order input to status for fastq-only orders."""
        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'samples': [{
                'internal_id': sample.get('internal_id'),
                'name': sample['name'],
                'application': sample['application'],
                'priority': sample['priority'],
                'comment': sample.get('comment'),
                'tumour': sample.get('tumour') or False,
                'sex': sample.get('sex'),
                'status': sample.get('status'),
            } for sample in data['samples']],
        }
        return status_data

    @classmethod
    def families_to_status(cls, data: dict) -> dict:
        """Convert order input to status interface input."""
        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'families': [],
        }
        families = cls.group_families(data['samples'])
        for family_name, family_samples in families.items():
            values = set(sample.get('priority', 'standard') for sample in family_samples)
            if len(values) > 1:
                raise ValueError(f"different 'priority' values: {family_name} - {values}")
            priority = values.pop()
            panels = set(panel for sample in family_samples for panel in sample['panels'])
            family = {
                'name': family_name,
                'priority': priority,
                'panels': list(panels),
                'samples': [{
                    'internal_id': sample.get('internal_id'),
                    'name': sample['name'],
                    'application': sample['application'],
                    'sex': sample['sex'],
                    'status': sample['status'],
                    'mother': sample.get('mother'),
                    'father': sample.get('father'),
                    'tumour': sample.get('tumour') or False,
                    'capture_kit': sample.get('capture_kit'),
                    'comment': sample.get('comment'),
                } for sample in family_samples],
            }

            status_data['families'].append(family)
        return status_data

    @staticmethod
    def group_families(samples: List[dict]) -> dict:
        """Group samples in families."""
        families = {}
        for sample in samples:
            if sample['family_name'] not in families:
                families[sample['family_name']] = []
            families[sample['family_name']].append(sample)
        return families

    def store_families(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                       families: List[dict]) -> List[models.Family]:
        """Store families and samples in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_families = []
        for family in families:
            new_family = self.status.add_family(
                name=family['name'],
                panels=family['panels'],
                priority=family['priority'],
            )
            new_family.customer = customer_obj
            new_families.append(new_family)

            family_samples = {}
            for sample in family['samples']:
                new_sample = self.status.add_sample(
                    name=sample['name'],
                    internal_id=sample['internal_id'],
                    sex=sample['sex'],
                    order=order,
                    ordered=ordered,
                    ticket=ticket,
                    priority=family['priority'],
                    comment=sample['comment'],
                )
                new_sample.customer = customer_obj
                with self.status.session.no_autoflush:
                    application_tag = sample['application']
                    new_sample.application_version = self.status.latest_version(application_tag)
                if new_sample.application_version is None:
                    raise OrderError(f"unknown application tag: {sample['application']}")
                family_samples[new_sample.name] = new_sample
                self.status.add(new_sample)

                new_delivery = self.status.add_delivery(destination='caesar', sample=new_sample)
                self.status.add(new_delivery)

            for sample in family['samples']:
                new_relationship = self.status.relate_sample(
                    family=new_family,
                    sample=family_samples[sample['name']],
                    status=sample['status'],
                    mother=family_samples[sample['mother']] if sample.get('mother') else None,
                    father=family_samples[sample['father']] if sample.get('father') else None,
                )
                self.status.add(new_relationship)
        self.status.add_commit(new_families)
        return new_families

    def store_samples(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                      samples: List[dict]) -> List[models.Sample]:
        """Store samples in the status database."""
        production_customer = self.status.customer('cust000')
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_samples = []
        for sample in samples:
            new_sample = self.status.add_sample(
                name=sample['name'],
                internal_id=sample['internal_id'],
                sex=sample['sex'] or 'unknown',
                order=order,
                ordered=ordered,
                ticket=ticket,
                priority=sample['priority'],
                comment=sample['comment'],
                tumour=sample['tumour'],
            )
            new_sample.customer = customer_obj
            with self.status.session.no_autoflush:
                new_sample.application_version = self.status.latest_version(sample['application'])
            new_samples.append(new_sample)

            if not new_sample.is_tumour:
                new_family = self.status.add_family(name=sample['name'], panels=['OMIM-AUTO'],
                                                    priority='research')
                new_family.customer = production_customer
                self.status.add(new_family)

                new_relationship = self.status.relate_sample(
                    family=new_family,
                    sample=new_sample,
                    status=sample['status'] or 'unknown',
                )
                self.status.add(new_relationship)

            new_delivery = self.status.add_delivery(destination='caesar', sample=new_sample)
            self.status.add(new_delivery)

        self.status.add_commit(new_samples)
        return new_samples

    def store_pools(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                    pools: List[dict]) -> List[models.Pool]:
        """Store pools in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_pools = []
        for pool in pools:
            with self.status.session.no_autoflush:
                application_version = self.status.latest_version(pool['application'])
            new_pool = self.status.add_pool(
                customer=customer_obj,
                name=pool['name'],
                order=order,
                ordered=ordered,
                ticket=ticket,
                application_version=application_version,
            )
            new_delivery = self.status.add_delivery(destination='caesar', pool=new_pool)
            self.store.add(new_delivery)
            new_pools.append(new_pool)
        self.store.add_commit(new_pools)
        return new_pools
