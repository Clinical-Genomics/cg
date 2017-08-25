from typing import List

from cg.exc import OrderError


class LimsHandler:

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
                    'volume': sample.get('volume'),
                    'concentration': sample.get('concentration'),
                    'source': sample.get('source') or 'NA',
                    'customer': data['customer'],
                    'comment': sample.get('comment'),
                    'tumour': sample.get('tumour') or False,
                    'pool': sample.get('pool'),
                    'index': sample.get('index'),
                    'index_number': sample.get('index_number'),
                }
            })
        return lims_data
    
    def process_lims(self, data: dict):
        """Process samples to add them to LIMS."""
        lims_data = self.to_lims(data)
        project_data = self.lims.add_project(lims_data)
        lims_map = self.lims.get_samples(projectlimsid=project_data['id'], map_ids=True)
        return project_data, lims_map
