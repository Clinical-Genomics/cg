from cg.apps.lims import LimsAPI
from cg.server.ext import lims as genologics_lims
from cg.store import Store, models


class InvoiceAPI:
    def __init__(self, db: Store, lims_api: LimsAPI, invoice_obj: models.Invoice):
        self.db = db
        self.lims_api = lims_api
        self.log = []
        self.invoice_obj = invoice_obj
        self.customer_obj = invoice_obj.customer
        self.record_type = ""
        self.raw_records = []
        self._set_record_type()

    def _set_record_type(self):
        """Define the record_type based on the invoice object.
        It can only be either pool or sample"""

        if self.invoice_obj.pools:
            self.raw_records = self.invoice_obj.pools
            self.record_type = "Pool"
        elif self.invoice_obj.samples:
            self.record_type = "Sample"
            self.raw_records = self.invoice_obj.samples

    def prepare_contact_info(self, costcenter):
        """Function to prepare contact info for a customer"""

        msg = (
            f"Could not open/generate invoice. Contact information missing in database for "
            f"customer {self.customer_obj.internal_id}. See log files."
        )

        customer = self.db.customer("cust999") if costcenter.lower() == "kth" else self.customer_obj
        user = customer.invoice_contact

        if not user:
            self.log.append(msg)
            return None

        contact = {
            "name": user.name,
            "email": user.email,
            "customer_name": customer.name,
            "reference": customer.invoice_reference,
            "address": customer.invoice_address,
        }

        if None in contact.values():
            self.log.append(msg)
            return None

        return contact

    def prepare(self, costcenter: str) -> dict:
        """Get information about an invoice to generate Excel report."""

        records = []
        pooled_samples = []

        for raw_record in self.raw_records:
            if self.record_type == "Pool":
                pooled_samples += genologics_lims.samples_in_pools(
                    raw_record.name, raw_record.ticket_number
                )
            record = self.prepare_record(
                costcenter=costcenter.lower(), discount=self.invoice_obj.discount, record=raw_record
            )
            if record:
                records.append(record)
            else:
                return None

        customer_obj = self.invoice_obj.customer
        contact = self.prepare_contact_info(costcenter)
        if not contact:
            return None
        return {
            "costcenter": costcenter,
            "project_number": getattr(customer_obj, f"project_account_{costcenter.lower()}"),
            "customer_id": customer_obj.internal_id,
            "customer_name": customer_obj.name,
            "agreement": customer_obj.agreement_registration,
            "invoice_id": self.invoice_obj.id,
            "contact": contact,
            "records": records,
            "pooled_samples": pooled_samples,
            "record_type": self.record_type,
        }

    def _discount_price(self, record, discount: int = 0):
        """Get discount price for a sample or pool."""

        if self.record_type == "Pool" or record.priority_human == "clinical trials":
            priority = "research"
        else:
            priority = record.priority_human

        full_price = getattr(record.application_version, f"price_{priority}")
        discount_factor = float(100 - discount) / 100

        if not full_price:
            return None
        return full_price * discount_factor

    def _cost_center_split_factor(self, price, costcenter, percent_kth, tag, version):
        """Split price based on cost center"""
        if price:
            try:
                if costcenter == "kth":
                    split_factor = percent_kth / 100
                else:
                    split_factor = (100 - percent_kth) / 100
                split_price = round(price * split_factor, 1)
            except ValueError:
                self.log.append(
                    f"Could not calculate price for samples with application "
                    f"tag/version: {tag}/{version}. Missing %KTH"
                )
                return None
        else:
            self.log.append(
                f"Could not get price for samples with application tag/version: {tag}/{version}."
            )
            return None
        return split_price

    def prepare_record(self, costcenter: str, discount: int, record):
        """Get invoice information for a specific sample or pool"""

        try:
            tag = record.application_version.application.tag
            version = str(record.application_version.version)
            percent_kth = record.application_version.application.percent_kth
            discounted_price = self._discount_price(record, discount)
        except ValueError:
            self.log.append(f"Application tag/version seems to be missing for sample {record.id}.")
            return None

        split_discounted_price = self._cost_center_split_factor(
            discounted_price, costcenter, percent_kth, tag, version
        )

        order = record.order
        ticket_number = record.ticket_number
        lims_id = None if self.record_type == "Pool" else record.internal_id
        priority = "research" if self.record_type == "Pool" else record.priority_human

        invoice_info = {
            "name": record.name,
            "lims_id": lims_id,
            "id": record.id,
            "application_tag": record.application_version.application.tag,
            "project": f"{order or 'NA'} ({ticket_number or 'NA'})",
            "date": record.received_at.date() if record.received_at else "",
            "price": split_discounted_price,
            "priority": priority,
        }
        if costcenter == "ki":
            price_kth = self._cost_center_split_factor(
                discounted_price, "kth", percent_kth, tag, version
            )
            invoice_info["price_kth"] = price_kth
            invoice_info["total_price"] = discounted_price
        return invoice_info

    def total_price(self) -> float:
        """Get the total price for all records in the invoice"""

        discount = self.invoice_obj.discount
        total_price = 0

        for record in self.raw_records:
            discount_price = self._discount_price(record, discount)
            if discount_price:
                total_price += discount_price
            else:
                return None

        return total_price
