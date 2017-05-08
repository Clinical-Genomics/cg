# -*- coding: utf-8 -*-
import logging

from dateutil.parser import parse as parse_date
from cglims import api
from cglims.config import basic_config
from cglims.exc import MissingLimsDataException
from cglims.export import export_case
from cglims.panels import convert_panels
from cglims.check import check_sample, process_samples
from genologics.entities import Process

from cg.exc import MultipleCustomersError

log = logging.getLogger(__name__)
config = basic_config


def connect(config):
    """Connect to LIMS."""
    return api.connect(config['cglims']['genologics'])


def case_sexes(lims_api, customer_id, family_name):
    """Fetch sample sex information from LIMS."""
    sample_sex = {}
    for lims_sample in lims_api.case(customer_id, family_name):
        sample_data = api.ClinicalSample(lims_sample).to_dict()
        sample_sex[sample_data['sample_id']] = sample_data['sex']
    return sample_sex


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


def export(lims_api, customer_id, family_id):
    lims_samples = lims_api.case(customer_id, family_id)
    case_data = export_case(lims_api, lims_samples)
    return case_data


def invoice(lims_samples):
    """Fetch information about invoicing."""
    customers = set()
    samples = []
    for lims_sample in lims_samples:
        sample_date = parse_date(lims_sample.date_received)
        try:
            customers.add(lims_sample.udf['customer'])
            data = dict(
                lims_id=lims_sample.id,
                date=sample_date.date(),
                application_tag=lims_sample.udf['Sequencing Analysis'],
                application_tag_version=int(lims_sample.udf['Application Tag Version']),
                priority=lims_sample.udf['priority'],
                project=lims_sample.project.name,
                name=lims_sample.name,
            )
        except KeyError as error:
            message = "Missing UDF value: {} - {}".format(lims_sample.id, error.message)
            raise MissingLimsDataException(message)
        samples.append(data)

    if len(customers) > 1:
        raise MultipleCustomersError(customers)
    return dict(samples=samples, customer_id=customers.pop())


def invoice_process(lims_api, process_id):
    """Get information from an invoice process."""
    lims_process = Process(lims_api, id=process_id)
    lims_data = process_samples(lims_process)

    lims_samples = {}
    for sample_data in lims_data:
        if sample_data['artifact'].name.startswith('Pool'):
            lims_artifact = sample_data['artifact']
            if lims_artifact.id not in lims_samples:
                lims_sample = sample_data['sample']
                lims_artifact.date_received = lims_sample.date_received
                lims_artifact.project = lims_sample.project
                udf_keys = ['customer', 'Sequencing Analysis', 'Application Tag Version',
                            'priority']
                for udf_key in udf_keys:
                    lims_artifact.udf[udf_key] = lims_sample.udf[udf_key]
                lims_samples[lims_artifact.id] = lims_artifact
        else:
            lims_samples[sample_data['sample'].id] = sample_data['sample']

    data = dict(
        lims_samples=lims_samples.values(),
        discount=float(lims_process.udf['Discount (%)']),
        lims_process=lims_process,
    )
    return data


def validate(lims_api, customer_id, family_name):
    """Get information used to validate a sample."""
    data = {}
    for lims_sample in lims_api.case(customer_id, family_name):
        sample = api.ClinicalSample(lims_sample)
        data[sample.sample_id] = dict(
            is_external=sample.apptag.is_external,
            is_panel=sample.apptag.is_panel,
            reads=sample.apptag.reads,
            is_low_input=sample.apptag.startswith('WGSLIN'),
        )
    return data


def start(lims_api, customer_id, family_name):
    """Fetch data relevant to starting an analysis."""
    statuses = set()
    is_externals = set()
    for lims_sample in lims_api.case(customer_id, family_name):
        sample = api.ClinicalSample(lims_sample)

        is_external = sample.apptag.is_external
        log.debug("%s is %s external", sample.sample_id, '' if is_external else 'not')
        is_externals.add(is_external)

        sample_status = sample.udf('priority')
        log.debug("%s has status %s", sample.sample_id, sample_status)
        statuses.add(sample_status)

    if len(is_externals) == 1:
        data = dict(is_external=is_externals.pop())
    else:
        # mix of internal and external samples
        data = dict(is_external=False)

    data['is_prio'] = True if ('express' in statuses) or ('priority' in statuses) else False
    return data
