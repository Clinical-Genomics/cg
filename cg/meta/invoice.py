# -*- coding: utf-8 -*-
from typing import List

from cg.apps import lims
from cg.store import Store, models


class InvoiceAPI():

    def __init__(self, db: Store, lims_api: lims.LimsAPI):
        self.db = db
        self.lims = lims_api

    def prepare_status(self, costcenter: str, sample_ids: List[str], discount: float=1.0):
        """Get invoice data from status store."""
        samples = [self.db.sample(sample_id) for sample_id in sample_ids]
        customers = set(sample.customer.internal_id for sample in samples)
        if len(customers) > 1:
            raise ValueError(f"multiple different customers: {', '.join(customers)}")
        customer_obj = samples[0].customer

        if costcenter == 'kth':
            contact_customer = self.db.customer('cust999')
        else:
            contact_customer = customer_obj
        contact_user = self.db.user(contact_customer.invoice_contact)

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
            'samples': [self._prepare_sample(sample) for sample in samples]
        }

    def _prepare_sample(self, costcenter: str, discount: float, sample_obj: models.Sample) -> dict:
        """Get invoice info about a sample."""
        full_price = getattr(sample_obj.application_version, f"price_{sample_obj.priority}")
        if costcenter == 'kth':
            split_factor = sample_obj.application_version.percent_kth / 100
            price = full_price * split_factor * discount
        else:
            split_factor = (100 - sample_obj.application_version.percent_kth) / 100
            price = full_price * split_factor * discount

        return {
            'name': sample_obj.name,
            'lims_id': sample_obj.internal_id,
            'application_tag': sample_obj.application_version.application.tag,
            'project': sample_obj.order,
            'date': sample_obj.received_at,
            'price': price,
        }

    def prepare_lims(self, process_id: str) -> dict:
        """Get invoice data from a LIMS process."""
        lims_process = self.lims.process(process_id)
        lims_ids = self.lims.process_samples(process_id)
        return {
            'lims_ids': lims_ids,
            'discount': ((100 - float(lims_process.udf['Discount (%)'])) / 100),
        }
