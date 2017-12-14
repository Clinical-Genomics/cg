# -*- coding: utf-8 -*-
from typing import List

from cg.apps import lims, invoice
from cg.store import Store, models
from cg.server.ext import lims as genologics_lims


class InvoiceAPI():

    def __init__(self, db: Store, lims_api: lims.LimsAPI):
        self.db = db
        self.lims_api = lims_api

    def prepare_(self, costcenter: str, invoice_obj: models.Invoice) -> dict:
        """Get information about an invoice to generate Excel report."""
        customer_obj = invoice_obj.customer
        if costcenter.lower() == 'kth':
            contact_customer = self.db.customer('cust999')
        else:
            contact_customer = customer_obj
        contact_user = self.db.user(customer_obj.invoice_contact)
        return {
            'costcenter': costcenter,
            'project_number': getattr(customer_obj, f"project_account_{costcenter.lower()}"),
            'customer_id': customer_obj.internal_id,
            'customer_name': customer_obj.name,
            'agreement': customer_obj.agreement_registration,
            'invoice_id': invoice_obj.id,
            'contact': {
                'name': contact_user.name,
                'email': contact_user.email,
                'customer_name': contact_customer.name,
                'reference': contact_customer.invoice_reference,
                'address': contact_customer.invoice_address,
            },
            'samples': [self.prepare_sample(
                            costcenter=costcenter.lower(),
                            discount=invoice_obj.discount,
                            sample_obj=sample,
                        ) for sample in invoice_obj.samples]
        }

    def prepare(self, costcenter: str, invoice_obj: models.Invoice) -> dict:
        """Get information about an invoice to generate Excel report."""

        records = []
        pooled_samples = []
        if invoice_obj.pools:
            for pool in invoice_obj.pools: 
                pooled_samples += genologics_lims.samples_in_pools(pool.name, pool.lims_project)
                records.append(self.prepare_record(
                                    costcenter=costcenter.lower(),
                                    discount=invoice_obj.discount,
                                    record=pool))
        elif invoice_obj.samples:
            for sample in invoice_obj.samples:
                records.append(self.prepare_record(
                                    costcenter=costcenter.lower(),
                                    discount=invoice_obj.discount,
                                    record=sample))




        customer_obj = invoice_obj.customer
        if costcenter.lower() == 'kth':
            contact_customer = self.db.customer('cust999')
        else:
            contact_customer = customer_obj
        contact_user = self.db.user(customer_obj.invoice_contact)
        return {
            'costcenter': costcenter,
            'project_number': getattr(customer_obj, f"project_account_{costcenter.lower()}"),
            'customer_id': customer_obj.internal_id,
            'customer_name': customer_obj.name,
            'agreement': customer_obj.agreement_registration,
            'invoice_id': invoice_obj.id,
            'contact': {
                'name': contact_user.name,
                'email': contact_user.email,
                'customer_name': contact_customer.name,
                'reference': contact_customer.invoice_reference,
                'address': contact_customer.invoice_address,
            },
            'records': records,
            'pooled_samples' : pooled_samples
            }

    def prepare_record(self, costcenter: str, discount: int, record: models.Sample):
        """Get information to invoice for a sample."""
        if type(record)==models.Pool:
            priority='research'
            lims_id = None
        elif type(record)==models.Sample:
            priority = record.priority_human
            lims_id = record.internal_id

        full_price = getattr(record.application_version, f"price_{priority}")
        if not discount:
            discount=0
        discount_factor = float(100 - discount) / 100
        if costcenter == 'kth':
            split_factor = record.application_version.application.percent_kth / 100
            price = full_price * split_factor * discount_factor
        else:
            split_factor = (100 - record.application_version.application.percent_kth) / 100
            price = full_price * split_factor * discount_factor

        return {
            'name': record.name,
            'lims_id': lims_id,
            'application_tag': record.application_version.application.tag,
            'project': f"{record.order or 'NA'} ({record.ticket_number or 'NA'})",
            'date': record.received_at,
            'price': round(price, 1),
        }

