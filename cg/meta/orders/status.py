import datetime as dt
from typing import List

from cg.exc import OrderError
from cg.store import models


class StatusHandler:

    @staticmethod
    def group_families(samples: List[dict]) -> dict:
        """Group samples in families."""
        families = {}
        for sample in samples:
            if sample['family_name'] not in families:
                families[sample['family_name']] = []
            families[sample['family_name']].append(sample)
        return families

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

    def store_families(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                       families: List[dict]) -> List[models.Family]:
        """Store families and samples in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_families = []
        for family in families:
            family_obj = self.status.find_family(customer_obj, family['name'])
            if family_obj:
                family_obj.panels = family['panels']
            else:
                family_obj = self.status.add_family(
                    name=family['name'],
                    panels=family['panels'],
                    priority=family['priority'],
                )
                family_obj.customer = customer_obj
                new_families.append(family_obj)

            family_samples = {}
            for sample in family['samples']:
                sample_obj = self.status.sample(sample['internal_id'])
                if sample_obj:
                    sample_obj.name = sample['name']
                    sample_obj.sex = sample['sex']
                    sample_obj.comment = sample['comment']
                    family_samples[sample_obj.name] = sample_obj
                else:
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
                        new_sample.is_external = True if application_tag[2] == 'X' else False
                    if new_sample.application_version is None:
                        raise OrderError(f"unknown application tag: {sample['application']}")
                    family_samples[new_sample.name] = new_sample
                    self.status.add(new_sample)

                    new_delivery = self.status.add_delivery(destination='caesar', sample=new_sample)
                    self.status.add(new_delivery)

            for sample in family['samples']:
                mother_obj = family_samples[sample['mother']] if sample.get('mother') else None
                father_obj = family_samples[sample['father']] if sample.get('father') else None
                with self.status.session.no_autoflush:
                    link_obj = self.status.link(family_obj.internal_id, sample['internal_id'])
                if link_obj:
                    link_obj.status = sample['status'] or link_obj.status
                    link_obj.mother = mother_obj or link_obj.mother
                    link_obj.father = father_obj or link_obj.father
                else:
                    new_link = self.status.relate_sample(
                        family=family_obj,
                        sample=family_samples[sample['name']],
                        status=sample['status'],
                        mother=mother_obj,
                        father=father_obj,
                    )
                    self.status.add(new_link)
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
            with self.status.session.no_autoflush:
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
                with self.status.session.no_autoflush:
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
                if application_version is None:
                    raise OrderError(f"unknown application: {pool['application']}")
            new_pool = self.status.add_pool(
                customer=customer_obj,
                name=pool['name'],
                order=order,
                ordered=ordered,
                ticket=ticket,
                application_version=application_version,
            )
            new_delivery = self.status.add_delivery(destination='caesar', pool=new_pool)
            self.status.add(new_delivery)
            new_pools.append(new_pool)
        self.status.add_commit(new_pools)
        return new_pools
