# -*- coding: utf-8 -*-
import logging
from xml.etree import ElementTree

from genologics.entities import Project, Researcher, Sample, Container, Containertype

log = logging.getLogger(__name__)
CONTAINER_TYPE_MAP = {'Tube': 2, '96 well plate': 1}
PROP2UDF = {
    "require_qcok": "Process only if QC OK",
    "application_tag": "Sequencing Analysis",
    "priority": "priority",
    "source": "Source",
    "comment": "Comment",
    "customer_id": "customer",
    "family_name": "familyID",
    "quantity": "Quantity",
    "tumour": "tumor",
}


class OrderHandler:

    def add_project(self, project_data, researcher_id='3'):
        """Submit a new order.

        Example:

            {
                'name': 'project name',
                'samples': [{
                    'name': '17081-II-1U',
                    "container": "96 well plate",
                    "container_name": "CMMS",
                    'udfs': {
                        'priority': 'standard',
                        'application_tag': 'WGTPCFC030',
                        'require_qcok': True,
                        'well_position': 'A:1',
                        'quantity': "2200",
                        'source': 'blood',
                        'customer': 'cust003',
                    },
                }]
            }

        Args:
            project_data (dict): project order data dict
            researcher_id (Optional[str]): id of research to link to the order

        Returns:
            genologics.entities.Project: new LIMS project instance
        """
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

    @classmethod
    def prepare(cls, project_data, researcher_id):
        """Convert API input to LIMS input data."""
        lims_data = {
            'name': project_data['name'],
            'researcher_id': researcher_id,
            'containers': [],
        }
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
                        'udfs': {}
                    }
                    for key, value in sample_data.items():
                        if key in PROP2UDF:
                            if isinstance(value, bool):
                                value = 'yes' if value else 'no'
                            new_sample[PROP2UDF[key]] = value

                    new_container['samples'].append(new_sample)
                lims_data['containers'].append(new_container)
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
