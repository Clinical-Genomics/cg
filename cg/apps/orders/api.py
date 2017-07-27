# -*- coding: utf-8 -*-
from cg.apps.lims import LimsAPI
from cg.store import Store
from .schema import ExternalProject, FastqProject, RerunProject, ScoutProject


class OrdersAPI():

    projects = {
        'external': ExternalProject(),
        'fastq': FastqProject(),
        'rerun': RerunProject(),
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

        if project_type != 'external':
            #lims_data = self.to_lims(data)
            #lims_project = self.lims.add_project(lims_data)
            #lims_samples = self.lims.get_samples(projectlimsid=lims_project.id)
            #lims_map = {lims_sample.name: lims_sample.id for lims_sample in lims_samples}
            #status_data = self.to_status(data, lims_map)
            pass
        else:
            pass
        status_data = self.to_status(data)
        new_families = self.status.add_order(status_data)
        self.status.commit()
        return {
        #    'lims_project': lims_project,
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
        for family in data['families']:
            for sample in family['samples']:
                lims_data['samples'].append({
                    'name': sample['name'],
                    'container': sample['container'],
                    'container_name': sample['container_name'],
                    'udfs': {
                        'family_name': family['name'],
                        'priority': family['priority'],
                        'application': sample['application'],
                        'require_qcok': family['require_qcok'],
                        'well_position': sample['well_position'],
                        'quantity': sample['quantity'],
                        'source': sample['source'],
                        'customer': data['customer'],
                    }
                })
        return lims_data

    @staticmethod
    def to_status(data: dict, lims_map: dict=None) -> dict:
        """Convert order input to status interface input."""
        status_data = {
            'customer': data['customer'],
            'name': data['name'],
            'families': [{
                'name': family['name'],
                'priority': family.get('priority', 'standard'),
                'panels': family['panels'],
                'samples': [{
                    'internal_id': (sample.get('internal_id') or
                                    (lims_map[sample['name']] if lims_map else None)),
                    'name': sample['name'],
                    'application': sample['application'],
                    'sex': sample['sex'],
                    'status': sample['status'],
                    'mother': sample.get('mother'),
                    'father': sample.get('father'),
                } for sample in family['samples']]
            } for family in data['families']]
        }
        return status_data
