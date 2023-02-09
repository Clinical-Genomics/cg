from cg.apps.lims import LimsAPI
from cg.server.ext import lims as genologics_lims
from cg.store import Store, models
from cg.constants.priority import PriorityTerms
from cg.constants.record_type import RecordType


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
        self.genologics_lims = genologics_lims
        self.invoice_info = dict()

    def _set_record_type(self):
        """Define the record_type based on the invoice object.
        It can only be either pool or sample"""
        if self.invoice_obj.pools:
            self.raw_records = self.invoice_obj.pools
            self.record_type = RecordType.Pool
        elif self.invoice_obj.samples:
            self.record_type = RecordType.Sample
            self.raw_records = self.invoice_obj.samples

    def get_customer(self, costcenter: str):
        return self.db.customer("cust999") if costcenter.lower() == "kth" else self.customer_obj

    def get_user(self, customer: models.Customer, msg: str):
        user = customer.invoice_contact
        if not user:
            self.log.append(msg)
            return None
        return user

    def get_contact(self, customer: models.Customer, user: models.User or None, msg: str) -> dict or None:
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

    def prepare_contact_info(self, costcenter: str):
        """Function to prepare contact info for a customer"""

        msg = (
            f"Could not open/generate invoice. Contact information missing in database for "
            f"customer {self.customer_obj.internal_id}. See log files."
        )
        customer = self.get_customer(costcenter=costcenter)
        user = self.get_user(customer=customer, msg=msg)
        contact = self.get_contact(user=user, customer=customer, msg=msg)
        return contact

    def prepare(self, costcenter: str) -> dict:
        """Get information about an invoice to generate Excel report."""

        records = []
        pooled_samples = []

        for raw_record in self.raw_records:
            if self.record_type == RecordType.Pool:
                pooled_samples += self.genologics_lims.samples_in_pools(
                    raw_record.name, raw_record.ticket
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
        priority = self.get_priority(record, for_discount_price=True)
        full_price = getattr(record.application_version, f"price_{priority}")
        discount_factor = 1 - discount / 100
        if not full_price:
            return None
        return round(full_price * discount_factor)

    def _cost_center_split_factor(self, price: int, costcenter: str, percent_kth: , tag: str, version: str):
        """Split price based on cost center"""
        if price:
            try:
                if costcenter == "kth":
                    split_factor = percent_kth / 100
                else:
                    split_factor = 1 - percent_kth / 100
                split_price = round(price * split_factor)
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
        application_info = self.get_application_info(record=record, discount=discount)
        split_discounted_price = self._cost_center_split_factor(
            price=application_info["discounted_price"],
            costcenter=costcenter,
            percent_kth=application_info["percent_kth"],
            tag=application_info["tag"],
            version=application_info["version"],
        )
        invoice_info = self.get_invoice_info(
            record=record,
            split_discounted_price=split_discounted_price,
            costcenter=costcenter,
            application_info=application_info,
        )
        self.set_invoice_info()
        return invoice_info

    def get_application_info(self, record, discount: int) -> dict or None:
        """Get the application information"""
        application_info = {}
        try:
            application_info["tag"] = record.application_version.application.tag
            application_info["version"] = str(record.application_version.version)
            application_info["percent_kth"] = record.application_version.application.percent_kth
            application_info["discounted_price"] = self._discount_price(record, discount)
        except ValueError:
            self.log.append(f"Application tag/version seems to be missing for sample {record.id}.")
            return None
        return application_info

    def get_ticket(self, record) -> str:
        return record.ticket if self.record_type == RecordType.Pool else record.original_ticket

    def get_lims_id(self, record) -> str:
        return None if self.record_type == RecordType.Pool else record.internal_id

    def get_priority(self, record, for_discount_price: bool = False) -> str:
        if self.customer_obj.internal_id == "cust032":
            priority = PriorityTerms.STANDARD
        elif self.record_type == RecordType.Pool or (
            record.priority_human == "clinical trials" and for_discount_price
        ):
            priority = PriorityTerms.RESEARCH
        else:
            priority = record.priority_human
        return priority

    def get_invoice_info(
        self, record, split_discounted_price: int, costcenter: str, application_info: dict
    ) -> dict:
        """Generate the invoice_info"""
        order = record.order
        ticket = self.get_ticket(record)
        lims_id = self.get_lims_id(record)
        priority = self.get_priority(record)

        invoice_info = {
            "name": record.name,
            "lims_id": lims_id,
            "id": record.id,
            "application_tag": record.application_version.application.tag,
            "project": f"{order or 'NA'} ({ticket or 'NA'})",
            "date": record.received_at.date() if record.received_at else "",
            "price": split_discounted_price,
            "priority": priority,
        }
        if costcenter == "ki":
            price_kth = self._cost_center_split_factor(
                price=application_info["discounted_price"],
                costcenter="kth",
                percent_kth=["percent_kth"],
                tag=application_info["tag"],
                version=application_info["version"],
            )
            invoice_info["price_kth"] = price_kth
            invoice_info["total_price"] = application_info["discounted_price"]

        return self.invoice_info

    def set_invoice_info(self, invoice_info: dict):
        """Set invoice_info"""
        self.invoice_info = invoice_info

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
