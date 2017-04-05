# -*- coding: utf-8 -*-
import logging

import click

from cg import apps
from .render import render_xlsx

log = logging.getLogger(__name__)


@click.command()
@click.option('-c', '--costcenter', default='kth')
@click.option('-o', '--out', 'xlsx_path', type=click.Path(), required=True)
@click.argument('customer_id')
@click.argument('sample_ids', nargs=-1)
@click.pass_context
def invoice(context, costcenter, xlsx_path, customer_id, sample_ids):
    """Generate invoice for a set of samples for a customer."""
    lims_api = apps.lims.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)
    data = admin_db.invoice(customer_id, costcenter=costcenter)
    data['samples'] = apps.lims.invoice(lims_api, sample_ids)
    for sample_data in data['samples']:
        log.info("working on sample: %s", sample_data['lims_id'])
        sample_data['price'] = admin_db.price(sample_data['application_tag'],
                                              sample_data['application_tag_version'],
                                              sample_data['priority'])
    workbook = render_xlsx(data, costcenter)
    workbook.save(xlsx_path)
