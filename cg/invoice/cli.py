# -*- coding: utf-8 -*-
from __future__ import division
import hashlib
import logging

import click
from cglims.exc import MissingLimsDataException

from cg import apps
from .render import render_xlsx

log = logging.getLogger(__name__)
COSTCENTERS = ['kth', 'ki']


class MismatchingCustomersError(Exception):
    pass


# @click.command()
# @click.option('-c', '--costcenter', type=click.Choice(COSTCENTERS), default='kth')
# @click.option('-o', '--out', 'xlsx_path', type=click.Path(), required=True)
# @click.option('-d', '--discount', type=float, help='Discount price for each sample')
# @click.argument('customer_id')
# @click.argument('sample_ids', nargs=-1)
# @click.pass_context
# def invoice(context, costcenter, xlsx_path, discount, customer_id, sample_ids):
#     """Generate invoice for a set of samples for a customer."""
#     lims_api = apps.lims.connect(context.obj)
#     admin_db = apps.admin.Application(context.obj)

#     lims_samples = [lims_api.sample(sample_id) for sample_id in sample_ids]
#     try:
#         generate_invoice(lims_api, admin_db, customer_id, lims_samples, costcenter, xlsx_path,
#                          discount=discount)
#     except MismatchingCustomersError as error:
#         log.error(error.message)
#         context.abort()


@click.command()
@click.option('-c', '--customer', 'customer_id')
@click.argument('process_id')
@click.pass_context
def invoice(context, customer_id, process_id):
    """Generate invoices from a LIMS process."""
    lims_api = apps.lims.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)
    lims_data = apps.lims.invoice_process(lims_api, process_id)

    customer_id = customer_id or lims_data['customer_id']
    if customer_id is None:
        log.error('You need to provide a customer for the invoice')
        context.abort()
    lims_samples = lims_data['lims_samples']
    new_invoices = []
    for costcenter in ['kth', 'ki']:
        try:
            invoice_data = generate_invoice(lims_api, admin_db, customer_id, lims_samples,
                                            costcenter, discount=lims_data['discount'])
            invoice_data['customer_id'] = customer_id
            new_invoices.append(invoice_data)
        except (MismatchingCustomersError, MissingLimsDataException) as error:
            log.error(error.message)
            context.abort()

    for invoice_data in new_invoices:
        new_invoice = admin_db.add_invoice(invoice_data)
        log.info("created new %s invoice: %s", new_invoice.invoice_id)


def generate_invoice(lims_api, admin_db, customer_id, lims_samples, costcenter, discount=None):
    """Generate an invoice from a list of samples."""
    invoice_data = admin_db.invoice(customer_id, costcenter=costcenter)
    invoice_data['samples'] = apps.lims.invoice(lims_samples)

    hash_factory = hashlib.sha256()
    sample_list = [sample_data['lims_id'] for sample_data in invoice_data['samples']]
    samples_str = ''.join(sample_list)
    hash_factory.update(samples_str.encode())
    hash_factory.update(costcenter.encode())
    invoice_data['invoice_id'] = hash_factory.hexdigest()[:10]

    for data in invoice_data['samples']:
        log.debug("including sample: %s", data['lims_id'])
        if data['customer'] != customer_id:
            message = "mismatching customer: %s - %s", data['lims_id'], data['customer']
            raise MismatchingCustomersError(message)
        log.info("working on sample: %s", data['lims_id'])
        data['price'] = admin_db.price(data['application_tag'], data['application_tag_version'],
                                       data['priority'], costcenter=costcenter)
        if discount:
            data['price'] = data['price'] * ((100 - discount) / 100)
    invoice_data['costcenter'] = costcenter
    return invoice_data


def make_invoice(invoice_data, out_path):
    """Generate Excel invoice file."""
    workbook = render_xlsx(invoice_data)
    workbook.save(out_path)
