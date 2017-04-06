# -*- coding: utf-8 -*-
from __future__ import division
import datetime
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

    def price(self, app_tag, app_tag_version, priority, costcenter=None):
        """Get the price for a sample from the database."""
        version_obj = (self.ApplicationTagVersion.join(models.ApplicationTagVersion.apptag)
                           .filter(models.ApplicationTagVersion.version == app_tag_version,
                                   models.ApplicationTag.name == app_tag)).first()
        if version_obj:
            log.info("getting price from: %s (%s)", version_obj.apptag.name, version_obj.version)
            full_price = getattr(version_obj, "price_{}".format(priority))
            if costcenter == 'kth':
                return full_price * (version_obj.percent_kth / 100)
            elif costcenter == 'ki':
                return full_price * ((1 - version_obj.percent_kth) / 100)
            else:
                return full_price
        else:
            return None

    def invoice(self, customer_id, costcenter='kth'):
        """Get invoice information about a customer."""
        customer_obj = self.customer(customer_id)
        data = dict(
            name=customer_obj.name,
            contact=dict(
                name=customer_obj.invoice_contact.name,
                email=customer_obj.invoice_contact.email,
            ),
            reference=customer_obj.invoice_reference,
            project=getattr(customer_obj, "project_account_{}".format(costcenter)),
            agreement=customer_obj.agreement_registration,
            address=customer_obj.invoice_address,
        )
        return data

    def add_invoice(self, invoice_data):
        """Create a record for an invoice."""
        customer_obj = self.customer(invoice_data['customer_id'])
        new_invoice = models.Invoice(
            customer=customer_obj,
            invoice_id=invoice_data['invoice_id'],
            invoiced_at=datetime.date.today(),
            costcenter=invoice_data['costcenter'],
        )
        new_invoice.data = invoice_data
        invoice_obj = self.Invoice.save(new_invoice)
        return invoice_obj
