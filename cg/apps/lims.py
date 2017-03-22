# -*- coding: utf-8 -*-
import logging

from cglims import api
from cglims.config import basic_config
from cglims.exc import MissingLimsDataException
from cglims.panels import convert_panels
from cglims.check import check_sample, process_samples
from genologics.entities import Process

log = logging.getLogger(__name__)
config = basic_config


def connect(config):
    """Connect to LIMS."""
    return api.connect(config['cglims']['genologics'])


def extend_case(config_data, suffix):
    """Modify ids for downstream extensions."""
    config_data['family'] = "{}--{}".format(config_data['family'], suffix)
    for sample_data in config_data['samples']:
        sample_data['sample_id'] = "{}--{}".format(sample_data['sample_id'], suffix)


def sample_panels(lims_sample):
    """Get gene panels from a sample."""
    raw_panels = lims_sample.udf.get('Gene List')
    default_panels = raw_panels.split(';') if raw_panels else []
    additional_panel = lims_sample.udf.get('Additional Gene List')
    if additional_panel:
        default_panels.append(additional_panel)
    return default_panels


def check_samples(lims_api, samples, apptag_map):
    """Check if new samples in LIMS are correct."""
    for sample_dict in samples:
        lims_sample = sample_dict['sample']
        apptag_version = apptag_map[lims_sample.udf['Sequencing Analysis']]
        check_sample(lims_api, lims_sample, lims_artifact=sample_dict.get('artifact'),
                     update=True, version=apptag_version)


def process_to_samples(lims_api, process_id):
    """Get all LIMS samples and artifacts from a process."""
    lims_process = Process(lims_api, id=process_id)
    return process_samples(lims_process)


def check_config(lims_api, customer_id, family_id):
    """Check generation of pedigree config."""
    try:
        config_data = config(lims_api, customer_id, family_id)
    except MissingLimsDataException as error:
        log.error(error.args[0])
        return {'success': False, 'message': error.args[0]}
    except KeyError as error:
        log.error("UDF - %s", error.args[0])
        return {'success': False, 'message': error.args[0]}
    except AssertionError as error:
        if error.args[0].endswith('set()'):
            log.error('missing customer UDF')
            return {'success': False, 'message': 'missing customer UDF'}
        else:
            log.error(error.args[0])
            return {'success': False, 'message': error.args[0]}
    else:
        return {'success': True, 'data': config_data}
