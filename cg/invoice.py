# -*- coding: utf-8 -*-
from __future__ import division
import hashlib
import logging

import click
from cglims.exc import MissingLimsDataException

from cg import apps

log = logging.getLogger(__name__)
COSTCENTERS = ['kth', 'ki']


class MismatchingCustomersError(Exception):
    pass


@click.command()
@click.option('-c', '--customer', 'customer_id')
@click.argument('process_id')
@click.pass_context
def invoice(context, customer_id, process_id):
    """Generate invoices from a LIMS process."""
    log.debug("connecting to databases")
    lims_api = apps.lims.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)

    log.info("getting invoice data from process")
    lims_data = apps.lims.invoice_process(lims_api, process_id)

    customer_id = customer_id or lims_data['customer_id']
    if customer_id is None:
        log.error('You need to provide a customer for the invoice')
        context.abort()

    log.info("generate invoice data from LIMS and cgadmin")
    lims_samples = lims_data['lims_samples']
    try:
        invoice_data = generate_invoice(lims_api, admin_db, customer_id, lims_samples, discount=lims_data['discount'])
        invoice_data['customer_id'] = customer_id
    except (MismatchingCustomersError, MissingLimsDataException) as error:
        log.error(error.message)
        context.abort()

    new_invoice = admin_db.add_invoice(invoice_data)
    log.info("prepared new invoice: %s", new_invoice.invoice_id)


def generate_invoice(lims_api, admin_db, customer_id, lims_samples, discount=None):
    """Generate an invoice from a list of samples."""
    invoice_data = admin_db.invoice(customer_id)
    invoice_data['samples'] = apps.lims.invoice(lims_samples)

    hash_factory = hashlib.sha256()
    sample_list = [sample_data['lims_id'] for sample_data in invoice_data['samples']]
    samples_str = ''.join(sample_list)
    hash_factory.update(samples_str.encode())
    invoice_data['invoice_id'] = hash_factory.hexdigest()[:10]

    for data in invoice_data['samples']:
        log.debug("including sample: %s", data['lims_id'])
        if data['customer'] != customer_id:
            message = "mismatching customer: %s - %s", data['lims_id'], data['customer']
            raise MismatchingCustomersError(message)
        log.info("working on sample: %s", data['lims_id'])
        data['prices'] = admin_db.price(data['application_tag'], data['application_tag_version'],
                                        data['priority'], discount=discount)
    return invoice_data
