# -*- coding: utf-8 -*-
import logging
import sys
from datetime import datetime

import json

import click
from jinja2 import Environment, PackageLoader, select_autoescape

from cg.store import Store
from cg.store.models import Application, ApplicationVersion

LOG = logging.getLogger(__name__)


def validate_stdin(context, param, value):
    """Validate piped input contains some data.

    Raises:
        click.BadParameter: if STDIN is empty
    """
    # check if input is a file or stdin
    if value.name == '<stdin>' and sys.stdin.isatty():  # pragma: no cover
        # raise error if stdin is empty
        raise click.BadParameter('you need to pipe something to stdin')
    return value


@click.group()
@click.pass_context
def report(context):
    """Create Reports"""
    context.obj['db'] = Store(context.obj['database'])


@report.command()
@click.argument('in_data', callback=validate_stdin,
                type=click.File(encoding='utf-8', mode='r'), default='-', required=False)
@click.pass_context
def qc(context, in_data):
    """Generate a QC report for a case."""
    case_data = json.load(in_data)
    db = context.obj['db']
    qc_data = generate_qc_data(db, case_data)
    template_out = render_qc_report(qc_data)
    click.echo(template_out)


def generate_qc_data(database, case_data):
    """Generate qc data report."""
    delivery_data = dict(case_data)

    delivery_data['today'] = datetime.today()
    delivery_data['customer'] = database.Customer.filter_by(internal_id=case_data['customer']).first()
    used_applications = set()

    for sample in delivery_data['samples']:
        used_applications.add((sample['app_tag'], sample['app_tag_version']))
        sample['project'] = sample['project'].split()[0]

        if all(sample.get(date_key) for date_key in ['received_at', 'delivery_date']):
            processing_time = sample['delivery_date'].date() - sample['received_at']
            sample['processing_time'] = processing_time.days

        method_types = ['library_prep_method', 'sequencing_method', 'delivery_method']

        for method_type in method_types:
            document_raw = sample.get(method_type)

            if document_raw is None:
                continue

            doc_no, doc_version = [int(part) for part in document_raw.split(':')]
            method_obj = database.Method.filter_by(document=doc_no,
                                                   document_version=doc_version).first()
            if method_obj is None:
                LOG.warning("method not found in db: %s", document_raw)

            sample[method_type] = method_obj



    versions = []

    for apptag_id, apptag_version in used_applications:

        application = database.Application.filter_by(tag=apptag_id).first()
        application_id = application.id
        is_accredited = application.is_accredited
        version = database.ApplicationVersion\
            .filter_by(application_id=application_id, version=apptag_version).first()

        if version:
            versions.append(version)

    delivery_data['apptags'] = versions
    delivery_data['accredited'] = is_accredited
    return delivery_data


def render_qc_report(qc_data):
    env = Environment(
        loader=PackageLoader('cg', 'meta/report/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    print("2.9")
    template = env.get_template('report.html')
    template_out = template.render(**case_data)
    print("2.10")
    return template_out
