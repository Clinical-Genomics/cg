from typing import List

from cg.exc import OrderError


class LimsHandler:

    @staticmethod
    def to_lims(customer: str, samples: List[dict]) -> List[dict]:
        """Convert order input to lims interface input."""
        samples_lims = []
        for sample in samples:
            samples_lims.append({
                'name': sample['name'],
                'container': sample.get('container') or 'Tube',
                'container_name': sample.get('container_name'),
                'well_position': sample.get('well_position'),
                'index_sequence': sample.get('index_sequence'),
                'udfs': {
                    'family_name': sample.get('family_name') or 'NA',
                    'priority': sample.get('priority') or 'standard',
                    'application': sample['application'],
                    'require_qcok': sample.get('require_qcok') or False,
                    'quantity': sample.get('quantity'),
                    'volume': sample.get('volume'),
                    'concentration': sample.get('concentration'),
                    'source': sample.get('source') or 'NA',
                    'customer': customer,
                    'comment': sample.get('comment'),
                    'tumour': sample.get('tumour') or False,
                    'pool': sample.get('pool'),
                    'index': sample.get('index'),
                    'index_number': sample.get('index_number'),
                    'rml_plate_name': sample.get('rml_plate_name'),
                    'well_position_rml': sample.get('well_position_rml'),
                }
            })
        return samples_lims

    def process_lims(self, data: dict, samples: List[dict]):
        """Process samples to add them to LIMS."""
        samples_lims = self.to_lims(data['customer'], samples)
        project_data = self.lims.add_project(data['ticket'] or data['name'], samples_lims)
        lims_map = self.lims.get_samples(projectlimsid=project_data['id'], map_ids=True)
        return project_data, lims_map
