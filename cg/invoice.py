# -*- coding: utf-8 -*-
from __future__ import division
from datetime import date
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
        invoices = generate_invoices(lims_api, admin_db, lims_samples,
                                     discount=lims_data['discount'])
    except (MultipleCustomersError, MissingLimsDataException) as error:
        log.error(error.message)
        context.abort()

    invoice_ids = []
    for invoice_data in invoices:
        new_invoice = admin_db.add_invoice(invoice_data)
        log.info("prepared new invoice: %s", new_invoice.invoice_id)
        invoice_ids.append(new_invoice.invoice_id)

        # for sample_data in invoice_data['samples']:
        #     lims_sample = lims_api.sample(sample_data['lims_id'])
        #     lims_sample.udf['Invoice reference'] = new_invoice.invoice_id
        #     lims_sample.put()

    lims_data['lims_process'].udf['Invoice reference'] = ', '.join(invoice_ids)
    lims_data['lims_process'].udf['Invoicing date'] = date.today()
    lims_data['lims_process'].put()


def generate_invoices(lims_api, admin_db, lims_samples, discount=None):
    """Generate an invoice from a list of samples."""
    lims_data = apps.lims.invoice(lims_samples)
    base_invoice_data = admin_db.invoice(lims_data['customer_id'])
    base_invoice_data['customer_id'] = lims_data['customer_id']

    for data in lims_data['samples']:
        log.debug("including sample: %s", data['lims_id'])
        data['prices'] = admin_db.price(data['application_tag'], data['application_tag_version'],
                                        data['priority'], discount=discount)

    limit = 300000 if lims_data['customer_id'] == 'cust002' else 1000000000  # inf
    for samples_data in apps.admin.split_invoice(lims_data['samples'], limit=limit):
        invoice_data = base_invoice_data.copy()
        invoice_data['samples'] = samples_data
        yield invoice_data
