import logging
from typing import List

LOG = logging.getLogger(__name__)
SEX_MAP = {'male': 'M', 'female': 'F'}


class LimsHandler:

    @staticmethod
    def to_lims(customer: str, samples: List[dict]) -> List[dict]:
        """Convert order input to lims interface input."""
        samples_lims = []
        for sample in samples:
            LOG.debug(f"{sample['name']}: prepare LIMS input")
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
                    'concentration_weight': sample.get('concentration_weight'),
                    'source': sample.get('source') or 'NA',
                    'customer': customer,
                    'comment': sample.get('comment'),
                    'tumour': sample.get('tumour') or False,
                    'pool': sample.get('pool'),
                    'index': sample.get('index'),
                    'index_number': sample.get('index_number'),
                    'rml_plate_name': sample.get('rml_plate_name'),
                    'well_position_rml': sample.get('well_position_rml'),
                    'sex': SEX_MAP.get(sample.get('sex'), 'unknown'),
                    'organism': sample.get('organism'),
                    'organism_other': sample.get('organism_other'),
                    'elution_buffer': sample.get('elution_buffer'),
                    'reference_genome': sample.get('reference_genome'),
                    'extraction_method': sample.get('extraction_method'),
                    'verified_organism': sample.get('verified_organism'),
                }
            })
        return samples_lims

    def process_lims(self, data: dict, samples: List[dict]):
        """Process samples to add them to LIMS."""
        samples_lims = self.to_lims(data['customer'], samples)
        project_name = data['ticket'] or data['name']
        project_data = self.lims.submit_project(project_name, samples_lims)
        lims_map = self.lims.get_samples(projectlimsid=project_data['id'], map_ids=True)
        return project_data, lims_map
