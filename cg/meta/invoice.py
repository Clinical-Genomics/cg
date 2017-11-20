# -*- coding: utf-8 -*-
from typing import List

from cg.apps import lims, invoice
from cg.store import Store, models


class InvoiceAPI():

    def __init__(self, db: Store):
        self.db = db

    def prepare(self, costcenter: str, invoice_obj: models.Invoice) -> dict:
        """Get information about an invoice to generate Excel report."""
        customer_obj = invoice_obj.customer
        if costcenter == 'kth':
            contact_customer = self.db.customer('cust999')
        else:
            contact_customer = customer_obj

        contact_user = self.db.user(customer_obj.invoice_contact)
        return {
            'costcenter': costcenter,
            'project_number': getattr(customer_obj, f"project_account_{costcenter}"),
            'customer_id': customer_obj.internal_id,
            'customer_name': customer_obj.name,
            'agreement': customer_obj.agreement_registration,
            'contact': {
                'name': contact_user.name,
                'email': contact_user.email,
                'customer_name': contact_customer.name,
                'reference': contact_customer.invoice_reference,
                'address': contact_customer.invoice_address,
            },
            'samples': [self.prepare_sample(
                costcenter=costcenter,
                discount=invoice_obj.discount,
                sample_obj=sample,
            ) for sample in invoice_obj.samples]
        }

    def prepare_sample(self, costcenter: str, discount: int, sample_obj: models.Sample):
        """Get information to invoice for a sample."""
        full_price = getattr(sample_obj.application_version, f"price_{sample_obj.priority_human}")
        discount_factor = (100 - discount) / 100
        if costcenter == 'kth':
            split_factor = sample_obj.application_version.application.percent_kth / 100
            price = full_price * split_factor * discount_factor
        else:
            split_factor = (100 - sample_obj.application_version.application.percent_kth) / 100
            price = full_price * split_factor * discount_factor

        return {
            'name': sample_obj.name,
            'lims_id': sample_obj.internal_id,
            'application_tag': sample_obj.application_version.application.tag,
            'project': f"{sample_obj.order or 'NA'} ({sample_obj.ticket_number or 'NA'})",
            'date': sample_obj.received_at,
            'price': price,
        }
