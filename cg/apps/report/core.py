# -*- coding: utf-8 -*-
import logging

from datetime import datetime
import json

import click
from jinja2 import Environment, PackageLoader, select_autoescape

from cgadmin.store.models import ApplicationTag, ApplicationTagVersion

log = logging.getLogger(__name__)


@click.command()
@click.argument('in_data', type=click.File('r'), default='-')
@click.pass_context
def report(context, in_data):
    """Generate a QC report for a case."""
    admin_db = context.obj['db']
    case_data = json.load(in_data)
    template_out = export_report(admin_db, case_data)
    click.echo(template_out)


def export_report(admin_db, case_data):
    """Generate a delivery report."""
    case_data['today'] = datetime.today()
    case_data['customer'] = admin_db.Customer.filter_by(customer_id=case_data['customer']).first()

    apptag_ids = set()
    for sample in case_data['samples']:
        apptag_ids.add((sample['app_tag'], sample['app_tag_version']))
        method_types = ['library_prep_method', 'sequencing_method', 'delivery_method']
        for method_type in method_types:
            document_raw = sample.get(method_type)
            if document_raw is None:
                continue
            doc_no, doc_version = [int(part) for part in document_raw.split(':')]
            method_obj = admin_db.Method.filter_by(document=doc_no,
                                                   document_version=doc_version).first()
            if method_obj is None:
                log.warn("method not found in admin db: %s", document_raw)
            sample[method_type] = method_obj
            sample['project'] = sample['project'].split()[0]

        if all(sample.get(date_key) for date_key in ['received_at', 'delivery_date']):
            processing_time = sample['delivery_date'].date() - sample['received_at']
            sample['processing_time'] = processing_time.days

    versions = []
    for apptag_id, apptag_version in apptag_ids:
        version = (admin_db.ApplicationTagVersion.join(ApplicationTagVersion.apptag)
                           .filter(ApplicationTag.name == apptag_id,
                                   ApplicationTagVersion.version == apptag_version)
                           .first())
        if version:
            versions.append(version)
    is_accredited = all(version.is_accredited for version in versions)
    case_data['apptags'] = versions
    case_data['accredited'] = is_accredited

    env = Environment(
        loader=PackageLoader('cgadmin', 'report/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('report.html')
    template_out = template.render(**case_data)

    return template_out
