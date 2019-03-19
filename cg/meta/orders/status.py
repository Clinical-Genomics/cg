import datetime as dt
from typing import List

from cg.exc import OrderError
from cg.store import models


class StatusHandler:

    def __init__(self):
        self.status = None

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

        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'pools': []
        }

        # group pools
        pools = {}

        for sample in data['samples']:
            name = sample['pool']
            application = sample['application']
            data_analysis = sample['data_analysis']
            capture_kit = sample.get('capture_kit')

            if name not in pools:
                pools[name] = {}
                pools[name]['name'] = name
                pools[name]['applications'] = set()
                pools[name]['capture_kits'] = set()

            pools[name]['applications'].add(application)

            if capture_kit:
                pools[name]['capture_kits'].add(capture_kit)

        # each pool must only have one application type
        for pool in pools.values():

            applications = pool['applications']
            pool_name = pool['name']
            if len(applications) != 1:
                raise OrderError(f"different application in pool: {pool_name} - {applications}")

        # each pool must only have one capture kit
        for pool in pools.values():

            capture_kits = pool['capture_kits']
            pool_name = pool['name']

            if len(capture_kits) > 1:
                raise OrderError(f"different capture kits in pool: {pool_name} - {capture_kits}")

        for pool in pools.values():

            pool_name = pool['name']
            applications = pool['applications']
            application = applications.pop()
            capture_kits = pool['capture_kits']
            capture_kit = None

            if len(capture_kits) == 1:
                capture_kit = capture_kits.pop()

            status_data['pools'].append({
                'name': pool_name,
                'application': application,
                'data_analysis': data_analysis,
                'capture_kit': capture_kit,
            })
        return status_data

    @staticmethod
    def samples_to_status(data: dict) -> dict:
        """Convert order input to status for fastq-only/metagenome orders."""
        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'samples': [{
                'internal_id': sample.get('internal_id'),
                'name': sample['name'],
                'application': sample['application'],
                'data_analysis': sample['data_analysis'],
                'priority': sample['priority'],
                'comment': sample.get('comment'),
                'tumour': sample.get('tumour') or False,
                'sex': sample.get('sex'),
                'status': sample.get('status'),
            } for sample in data['samples']],
        }
        return status_data

    @staticmethod
    def microbial_samples_to_status(data: dict) -> dict:
        """Convert order input for microbial samples."""
        status_data = {
            'customer': data['customer'],
            'order': data['name'],
            'comment': data.get('comment'),
            'samples': [{
                'priority': sample_data['priority'],
                'name': sample_data['name'],
                'internal_id': sample_data.get('internal_id'),
                'organism_id': sample_data['organism'],
                'comment': sample_data.get('comment'),
                'reference_genome': sample_data['reference_genome'],
                'application': sample_data['application'],
                'data_analysis': sample_data['data_analysis'],
            } for sample_data in data['samples']]
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
            panels = set(panel for sample in family_samples for panel in sample.get('panels',
                                                                                    set()))
            family = {
                'name': family_name,
                'priority': priority,
                'panels': list(panels),
                'samples': [{
                    'internal_id': sample.get('internal_id'),
                    'name': sample['name'],
                    'application': sample['application'],
                    'data_analysis': sample.get('data_analysis'),
                    'sex': sample['sex'],
                    'status': sample.get('status'),
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
                    family_samples[sample['name']] = sample_obj
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
                        capture_kit=sample['capture_kit'],
                        data_analysis=sample['data_analysis'],
                        tumour=sample['tumour'],
                    )
                    new_sample.customer = customer_obj
                    with self.status.session.no_autoflush:
                        application_tag = sample['application']
                        new_sample.application_version = self.status.current_application_version(
                            application_tag)
                    if new_sample.application_version is None:
                        raise OrderError(f"Invalid application: {sample['application']}")
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
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_samples = []

        with self.status.session.no_autoflush:
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
                    data_analysis=sample['data_analysis'],
                )
                new_sample.customer = customer_obj
                application_tag = sample['application']
                application_version = self.status.current_application_version(application_tag)
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version = application_version
                new_samples.append(new_sample)

        self.status.add_commit(new_samples)
        return new_samples

    def store_fastq_samples(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                            samples: List[dict]) -> List[models.Sample]:
        """Store fast samples in the status database including family connection and delivery."""
        production_customer = self.status.customer('cust000')
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_samples = []

        with self.status.session.no_autoflush:
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
                    data_analysis=sample['data_analysis'],
                )
                new_sample.customer = customer_obj

                application_tag = sample['application']
                application_version = self.status.current_application_version(application_tag)
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample['application']}")
                new_sample.application_version = application_version
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

    def store_microbial_order(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                              lims_project: str, samples: List[dict],
                              comment: str = None) -> models.MicrobialOrder:
        """Store microbial samples in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        with self.status.session.no_autoflush:
            new_order = self.status.add_microbial_order(
                customer=customer_obj,
                name=order,
                ordered=ordered,
                internal_id=lims_project,
                ticket_number=ticket,
                comment=comment,
            )
            for sample_data in samples:
                application_tag = sample_data['application']
                application_version = self.status.current_application_version(application_tag)
                if application_version is None:
                    raise OrderError(f"Invalid application: {sample_data['application']}")

                organism = self.status.organism(sample_data['organism_id'])

                if not organism:
                    organism = self.status.add_organism(internal_id=sample_data[
                        'organism_id'], name=sample_data['organism_id'],
                                                        reference_genome=sample_data[
                                                            'reference_genome'])
                    self.status.add_commit(organism)

                new_sample = self.status.add_microbial_sample(
                    name=sample_data['name'],
                    internal_id=sample_data['internal_id'],
                    reference_genome=sample_data['reference_genome'],
                    comment=sample_data['comment'],
                    organism=organism,
                    application_version=application_version,
                    priority=sample_data['priority'],
                    data_analysis=sample_data['data_analysis'],
                )
                new_order.microbial_samples.append(new_sample)

        self.status.add_commit(new_order)
        return new_order

    def store_pools(self, customer: str, order: str, ordered: dt.datetime, ticket: int,
                    pools: List[dict]) -> List[models.Pool]:
        """Store pools in the status database."""
        customer_obj = self.status.customer(customer)
        if customer_obj is None:
            raise OrderError(f"unknown customer: {customer}")
        new_pools = []
        for pool in pools:
            with self.status.session.no_autoflush:
                application_version = self.status.current_application_version(pool['application'])
                if application_version is None:
                    raise OrderError(f"Invalid application: {pool['application']}")
            new_pool = self.status.add_pool(
                customer=customer_obj,
                name=pool['name'],
                order=order,
                ordered=ordered,
                ticket=ticket,
                application_version=application_version,
                data_analysis=pool['data_analysis'],
                capture_kit=pool['capture_kit'],
            )
            new_delivery = self.status.add_delivery(destination='caesar', pool=new_pool)
            self.status.add(new_delivery)
            new_pools.append(new_pool)
        self.status.add_commit(new_pools)
        return new_pools
