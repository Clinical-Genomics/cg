# -*- coding: utf-8 -*-
from __future__ import division
import datetime
import hashlib
import logging

from cgadmin.store import api, models
from cgadmin.report.core import export_report as export_report_api

log = logging.getLogger(__name__)


class Application(api.AdminDatabase):

    """Admin database API.

    Args:
        config (dict): CLI config object
    """

    def __init__(self, config):
        super(Application, self).__init__(config['cgadmin']['database'])

    def map_apptags(self, apptags):
        """Map application tags with latest versions.

        Args:
            admin_db (sqlservice.SQLClient)
        """
        apptag_map = {}
        for apptag_id in apptags:
            latest_version = self.latest_version(apptag_id)
            apptag_map[apptag_id] = latest_version.version
        return apptag_map

    def customer(self, customer_id):
        """Get a customer record from the database."""
        return self.Customer.filter_by(customer_id=customer_id).first()

    def export_report(self, case_data):
        """Pass-through to the original API function."""
        return export_report_api(self, case_data)

    def price(self, app_tag, app_tag_version, priority, discount=None):
        """Get the price for a sample from the database."""
        version_obj = (self.ApplicationTagVersion.join(models.ApplicationTagVersion.apptag)
                           .filter(models.ApplicationTagVersion.version == app_tag_version,
                                   models.ApplicationTag.name == app_tag)).first()
        if version_obj:
            log.info("getting price from: %s (%s)", version_obj.apptag.name, version_obj.version)
            full_price = getattr(version_obj, "price_{}".format(priority))
            discount_factor = ((100 - discount) / 100) if discount else 1
            prices = dict(
                kth=full_price * (version_obj.percent_kth / 100) * discount_factor,
                ki=full_price * ((100 - version_obj.percent_kth) / 100) * discount_factor,
                full=full_price * discount_factor,
                discount_factor=discount_factor,
            )
            return prices
        else:
            return None

    def invoice(self, customer_id):
        """Get invoice information about a customer."""
        customer_obj = self.customer(customer_id)
        kth_customer = self.customer('cust999')
        data = dict(
            customer_name=customer_obj.name,
            contact=dict(
                ki=dict(
                    name=customer_obj.invoice_contact.name,
                    email=customer_obj.invoice_contact.email,
                    customer_name=customer_obj.name,
                    reference=customer_obj.invoice_reference,
                    address=customer_obj.invoice_address,
                ),
                kth=dict(
                    name=kth_customer.invoice_contact.name,
                    email=kth_customer.invoice_contact.email,
                    customer_name=kth_customer.name,
                    reference=kth_customer.invoice_reference,
                    address=kth_customer.invoice_address,
                ),
            ),
            agreement=customer_obj.agreement_registration,
        )
        return data

    def add_invoice(self, invoice_data):
        """Create a record for an invoice."""
        hash_factory = hashlib.sha256()
        sample_list = [sample_data['lims_id'] for sample_data in invoice_data['samples']]
        samples_str = ''.join(sample_list)
        hash_factory.update(samples_str.encode())
        invoice_data['invoice_id'] = hash_factory.hexdigest()[:10]

        customer_obj = self.customer(invoice_data['customer_id'])
        new_invoice = models.Invoice(
            customer=customer_obj,
            invoice_id=invoice_data['invoice_id'],
            invoiced_at=datetime.date.today(),
        )
        new_invoice.data = invoice_data
        invoice_obj = self.Invoice.save(new_invoice)
        return invoice_obj


def split_invoice(samples_data, limit=300000):
    """Split invoice based on a cost limit."""
    current_slice = []
    price_sum = 0
    for sample_data in samples_data:
        sample_price = sample_data['prices']['kth'] + sample_data['prices']['ki']

        if price_sum + sample_price > limit:
            yield current_slice
            current_slice = []
            price_sum = 0

        current_slice.append(sample_data)
        price_sum += sample_price

    yield current_slice
