# -*- coding: utf-8 -*-
from cglims import api
from cglims.config import basic_config
from cglims.panels import convert_panels

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
