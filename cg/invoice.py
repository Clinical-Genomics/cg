# -*- coding: utf-8 -*-
from __future__ import division
import hashlib
import logging

import click
from cglims.exc import MissingLimsDataException

from cg import apps
from cg.exc import MultipleCustomersError

log = logging.getLogger(__name__)
COSTCENTERS = ['kth', 'ki']


@click.command()
@click.argument('process_id')
@click.pass_context
def invoice(context, process_id):
    """Generate invoices from a LIMS process."""
    log.debug("connecting to databases")
    lims_api = apps.lims.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)

    log.info("getting invoice data from process")
    lims_data = apps.lims.invoice_process(lims_api, process_id)

    log.info("generate invoice data from LIMS and cgadmin")
    lims_samples = lims_data['lims_samples']
    try:
        invoice_data = generate_invoice(lims_api, admin_db, lims_samples,
                                        discount=lims_data['discount'])
    except (MultipleCustomersError, MissingLimsDataException) as error:
        log.error(error.message)
        context.abort()

    new_invoice = admin_db.add_invoice(invoice_data)
    log.info("prepared new invoice: %s", new_invoice.invoice_id)


def generate_invoice(lims_api, admin_db, lims_samples, discount=None):
    """Generate an invoice from a list of samples."""
    lims_data = apps.lims.invoice(lims_samples)
    invoice_data = admin_db.invoice(lims_data['customer_id'])
    invoice_data.update(lims_data)

    hash_factory = hashlib.sha256()
    sample_list = [sample_data['lims_id'] for sample_data in invoice_data['samples']]
    samples_str = ''.join(sample_list)
    hash_factory.update(samples_str.encode())
    invoice_data['invoice_id'] = hash_factory.hexdigest()[:10]

    for data in invoice_data['samples']:
        log.debug("including sample: %s", data['lims_id'])
        data['prices'] = admin_db.price(data['application_tag'], data['application_tag_version'],
                                        data['priority'], discount=discount)
    return invoice_data
