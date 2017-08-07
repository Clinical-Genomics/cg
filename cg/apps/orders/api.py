# -*- coding: utf-8 -*-
from typing import List

from cg.apps.lims import LimsAPI
from cg.store import Store
from .schema import ExternalProject, FastqProject, RmlProject, ScoutProject


class OrdersAPI():

    projects = {
        'external': ExternalProject(),
        'fastq': FastqProject(),
        'rml': RmlProject(),
        'scout': ScoutProject(),
    }

    def __init__(self, lims: LimsAPI, status: Store):
        self.lims = lims
        self.status = status

    def accept(self, project_type: str, data: dict) -> dict:
        """Accept a new project."""
        errors = self.validate(project_type, data)
        if errors:
            return errors

        if project_type in ('external', 'scout'):
            status_data = self.families_to_status(data)
        else:
            status_data = self.samples_to_status(data)

        if project_type != 'external':
            lims_data = self.to_lims(data)
            lims_project = self.lims.add_project(lims_data)
            lims_samples = self.lims.get_samples(projectlimsid=lims_project.id)
            lims_map = {lims_sample.name: lims_sample.id for lims_sample in lims_samples}
        else:
            lims_project = None
            lims_map = {}

        for family in status_data['families']:
            for sample in family['samples']:
                sample['internal_id'] = lims_map.get(sample['name']) or sample['internal_id']

        new_families = self.status.add_order(status_data)
        self.status.commit()
        return {
            'lims_project': lims_project,
            'families': new_families,
        }

    @classmethod
    def validate(cls, project_type: str, data: dict) -> dict:
        """Validate input against a particular schema."""
        errors = cls.projects[project_type].validate(data)
        return errors

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
                'container': sample['container'],
                'container_name': sample.get('container_name'),
                'well_position': sample.get('well_position'),
                'udfs': {
                    'family_name': sample.get('family_name'),
                    'priority': sample['priority'],
                    'application': sample['application'],
                    'require_qcok': sample.get('require_qcok') or False,
                    'quantity': sample.get('quantity'),
                    'volume': data.get('volume'),
                    'concentration': data.get('concentration'),
                    'source': sample['source'],
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
    def samples_to_status(self, data: dict) -> dict:
        """Convert order input to status for fastq-only orders."""
        status_data = {
            'customer': data['customer'],
            'name': data['name'],
            'samples': [{
                'internal_id': sample.get('internal_id'),
                'name': sample['name'],
                'application': sample['application'],
                'tumour': sample.get('tumour') or False,
            } for sample in data['samples']],
        }
        return status_data

    @classmethod
    def families_to_status(cls, data: dict) -> dict:
        """Convert order input to status interface input."""
        status_data = {
            'customer': data['customer'],
            'name': data['name'],
            'families': [],
        }
        families = cls.group_families(data['samples'])
        for family_name, family_samples in families.items():
            family_options = {}
            for field in ['priority', 'panels']:
                values = set(sample[field] for sample in family_samples)
                if len(values) > 1:
                    raise ValueError(f"different '{field}' values: {family_name} - {values}")
                family_options[field] = values.pop()

            family = {
                'name': family_name,
                'priority': family_options['priority'],
                'panels': family_options['panels'],
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
