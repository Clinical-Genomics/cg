# -*- coding: utf-8 -*-
import datetime as dt

import click


class CustomerImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(customer):
        return {
            'internal_id': customer.customer_id,
            'name': customer.name,
            'scout_access': customer.scout_access,
            'agreement_date': (dt.datetime.combine(customer.agreement_date, dt.time()) if
                               customer.agreement_date else None),
            'agreement_registration': customer.agreement_registration,
            'invoice_address': customer.invoice_address,
            'invoice_reference': customer.invoice_reference,
            'organisation_number': customer.organisation_number,
            'project_account_ki': customer.project_account_ki,
            'project_account_kth': customer.project_account_kth,
            'uppmax_account': customer.uppmax_account,

            'primary_contact': (customer.primary_contact.email if
                                customer.primary_contact else None),
            'delivery_contact': (customer.delivery_contact.email if
                                 customer.delivery_contact else None),
            'invoice_contact': (customer.invoice_contact.email if
                                customer.invoice_contact else None),
        }

    def status(self, data):
        record = self.db.Customer(**data)
        return record

    def records(self):
        query = self.admin.Customer
        count = query.count()
        with click.progressbar(query, length=count, label='customers') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                if not self.db.customer(data['internal_id']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
