# -*- coding: utf-8 -*-
from copy import deepcopy
import logging

from genologics.entities import Project, Researcher, Sample, Container, Containertype
from xml.etree import ElementTree

from .udfs import PROP2UDF

log = logging.getLogger(__name__)
CONTAINER_TYPE_MAP = {'Tube': 2, '96 well plate': 1}


class LimsProject():

    def __init__(self, lims_api):
        self.lims = lims_api

    def __call__(self, project_data, researcher_id='3'):
        """Submit an order."""
        lims_data = self.prepare(project_data, researcher_id)
        lims_project = self.submit(lims_data)
        return lims_project

    def submit(self, data):
        """Submit a new project with samples to LIMS."""
        log.debug('creating LIMS project')
        lims_researcher = Researcher(self.lims, id=data['researcher_id'])
        lims_project = Project.create(self.lims, researcher=lims_researcher, name=data['name'])
        log.info("created new LIMS project: %s", lims_project.id)

        for container_data in data['containers']:
            log.debug('creating LIMS container')
            container_type = Containertype(lims=self.lims, id=container_data['type'])
            lims_container = Container.create(lims=self.lims, name=container_data['name'],
                                              type=container_type)
            log.info("created new LIMS container: %s", lims_container.id)

            for sample_data in container_data['samples']:
                log.debug("creating LIMS sample: %s", sample_data['name'])
                raw_sample = Sample._create(self.lims, creation_tag='samplecreation',
                                            name=sample_data['name'], project=lims_project)

                log.debug('adding sample UDFs')
                for udf_key, udf_value in sample_data['udfs'].items():
                    raw_sample.udf[udf_key] = udf_value

                position = sample_data['well_position']
                lims_sample = self._save_sample(raw_sample, lims_container, position)
                log.info("created new LIMS sample: %s -> %s", lims_sample.name, lims_sample.id)
        return lims_project

    def _save_sample(self, instance, container, position):
        """Create an instance of Sample from attributes then post it to the LIMS"""
        location = ElementTree.SubElement(instance.root, 'location')
        ElementTree.SubElement(location, 'container', dict(uri=container.uri))
        position_element = ElementTree.SubElement(location, 'value')
        position_element.text = position
        data = self.lims.tostring(ElementTree.ElementTree(instance.root))
        instance.root = self.lims.post(uri=self.lims.get_uri(Sample._URI), data=data)
        instance._uri = instance.root.attrib['uri']
        return instance

    @classmethod
    def prepare(cls, project_data, researcher_id):
        """Convert API input to LIMS input data."""
        lims_data = {
            'name': project_data['name'],
            'researcher_id': researcher_id,
            'containers': [],
        }
        # handle orders with families included
        if 'families' in project_data:
            project_data = cls.populate_family(project_data)
        tubes, plates = cls.group_containers(project_data['samples'])
        # "96 well plate" = container type "1"; Tube = container type "2"
        for container_type, containers in [('1', plates), ('2', tubes)]:
            for container_name, samples in containers.items():
                new_container = {
                    'name': container_name,
                    'type': container_type,
                    'samples': [],
                }
                for sample_data in samples:
                    location = sample_data.get('well_position')
                    if sample_data['container'] == '96 well plate' and location is None:
                        message = f"missing 'well_position' for sample: {sample_data['name']}"
                        raise ValueError(message)
                    new_sample = {
                        'name': sample_data['name'],
                        'location': location or '1:1',
                        'udfs': {
                            PROP2UDF['customer']: sample_data['customer'],
                        }
                    }
                    for key, value in sample_data.items():
                        if key in PROP2UDF:
                            if isinstance(value, bool):
                                value = 'yes' if value else 'no'
                            elif isinstance(value, list):
                                value = ','.join(value)
                            new_sample[PROP2UDF[key]] = value

                    new_container['samples'].append(new_sample)
                lims_data['containers'].append(new_container)
        return lims_data

    @staticmethod
    def poulate_family(project_data):
        """Fillin info on family level for samples."""
        new_data = deepcopy(project_data)
        new_data['samples'] = []
        for family_data in new_data['families']:
            for sample_data in family_data['samples']:
                sample_data['panels'] = family_data['panels']
                sample_data['famliy_name'] = family_data['name']
                sample_data['priority'] = family_data['priority']
                sample_data['require_qcok'] = family_data.get('require_qcok')
            new_data['samples'].append(sample_data)
        return new_data

    @classmethod
    def prepare_scout(cls, project_data):
        """Prepare input for a Scout project order."""
        new_data = cls.populate_family(project_data)
        lims_data = cls.prepare(new_data)
        return lims_data

    @staticmethod
    def group_containers(samples):
        """Group samples by containers."""
        tubes = {}
        plates = {}
        for sample_data in samples:
            if sample_data['container'] == 'Tube':
                # detected tube: name after sample unless specified
                container_name = sample_data.get('container_name') or sample_data['name']
                tubes[container_name] = [sample_data]
            elif sample_data['container'] == '96 well plate':
                # detected plate: require container name
                if sample_data['container_name'] not in plates:
                    plates[sample_data['container_name']] = []
                plates[sample_data['container_name']].append(sample_data)
            else:
                raise ValueError(f"unknown container type: {sample_data['container']}")
        return tubes, plates
