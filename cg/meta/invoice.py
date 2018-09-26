# -*- coding: utf-8 -*-
from typing import List

from cg.apps import lims, invoice
from cg.store import Store, models
from cg.server.ext import lims as genologics_lims


class InvoiceAPI():

    def __init__(self, db: Store, lims_api: lims.LimsAPI):
        self.db = db
        self.lims_api = lims_api






    def prepare(self, costcenter: str, invoice_obj: models.Invoice) -> dict:
        """Get information about an invoice to generate Excel report."""

        records = []
        pooled_samples = []
        record_type = ''
        if invoice_obj.pools:
            record_type = 'Pool'
            for pool in invoice_obj.pools: 
                pooled_samples += genologics_lims.samples_in_pools(pool.name, pool.lims_project)
                records.append(self.prepare_record(
                                    costcenter=costcenter.lower(),
                                    discount=invoice_obj.discount,
                                    record=pool))
        elif invoice_obj.samples:
            record_type = 'Prov'
            for sample in invoice_obj.samples:
                records.append(self.prepare_record(
                                    costcenter=costcenter.lower(),
                                    discount=invoice_obj.discount,
                                    record=sample))


        customer_obj = invoice_obj.customer
        if costcenter.lower() == 'kth':
            contact_customer = self.db.customer('cust999')
            contact_user = self.db.user('valtteri.wirta@ki.se')
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
            'pooled_samples' : pooled_samples,
            'record_type' : record_type
            }

    def prepare_record(self, costcenter: str, discount: int, record: models.Sample):
        """Get information to invoice for a sample."""
        if type(record)==models.Pool:
            lims_id = None
            priority = 'research'
        elif type(record)==models.Sample:
            lims_id = record.internal_id
            priority = record.priority_human

        discounted_price = self.get_price(discount, record)
        if costcenter == 'kth':
            split_factor = record.application_version.application.percent_kth / 100
        else:
            split_factor = (100 - record.application_version.application.percent_kth) / 100
        price = discounted_price * split_factor
        if record.received_at:
            recieved = record.received_at.date()
        else:
            recieved = ''
        return {
            'name': record.name,
            'lims_id': lims_id,
            'id':record.id,
            'application_tag': record.application_version.application.tag,
            'project': f"{record.order or 'NA'} ({record.ticket_number or 'NA'})",
            'date': recieved,
            'price': round(price, 1),
            'priority':priority
        }


    def get_price(self, discount: int, record: models.Sample):
        """Get discount price for a sample."""
        if type(record)==models.Pool:
            priority='research'
        elif type(record)==models.Sample:
            priority = record.priority_human

        full_price = getattr(record.application_version, f"price_{priority}")
        if not discount:
            discount=0
        discount_factor = float(100 - discount) / 100

        return full_price * discount_factor


    def total_price(self, invoice_obj: models.Invoice) -> float:
        discount = invoice_obj.discount
        total_price = 0
        if invoice_obj.pools:
            for record in invoice_obj.pools:
                total_price += self.get_price(discount, record)
        elif invoice_obj.samples:
            for record in invoice_obj.samples:
                total_price += self.get_price(discount, record)
        return total_price
