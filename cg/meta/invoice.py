from typing import Any

from pydantic.v1 import ValidationError

from cg.apps.lims import LimsAPI
from cg.constants.constants import CustomerId
from cg.constants.invoice import CostCenters
from cg.constants.priority import PriorityTerms
from cg.constants.sequencing import RecordType
from cg.models.invoice.invoice import (
    InvoiceApplication,
    InvoiceContact,
    InvoiceInfo,
    InvoiceReport,
)
from cg.server.ext import FlaskLims
from cg.server.ext import lims as genologics_lims
from cg.store.models import Customer, Invoice, Pool, Sample, User
from cg.store.store import Store


class InvoiceAPI:
    def __init__(self, db: Store, lims_api: LimsAPI, invoice_obj: Invoice):
        self.db = db
        self.lims_api = lims_api
        self.log = []
        self.invoice_obj = invoice_obj
        self.customer_obj = invoice_obj.customer
        self.record_type = ""
        self.raw_records = []
        self._set_record_type()
        self.genologics_lims: FlaskLims = genologics_lims
        self.invoice_info: InvoiceInfo | None = None

    def _set_record_type(self):
        """Define the record_type based on the invoice object.
        It can only be either pool or sample."""
        if self.invoice_obj.pools:
            self.raw_records = self.invoice_obj.pools
            self.record_type = RecordType.Pool
        elif self.invoice_obj.samples:
            self.record_type = RecordType.Sample
            self.raw_records = self.invoice_obj.samples

    def get_customer_by_cost_center(self, cost_center: str) -> Customer | str:
        """Return the costumer based on cost center."""
        return (
            self.db.get_customer_by_internal_id(customer_internal_id=CustomerId.CUST999)
            if cost_center.lower() == CostCenters.kth
            else self.customer_obj
        )

    def get_customer_invoice_contact(self, customer: Customer, msg: str) -> Any:
        """Return the customer invoice contact."""
        if not customer.invoice_contact:
            self.log.append(msg)
            return None
        return customer.invoice_contact

    def get_contact(
        self, customer: Customer, customer_invoice_contact: User | None, msg: str
    ) -> InvoiceContact | None:
        """Return the contact information."""
        try:
            contact = InvoiceContact(
                name=customer_invoice_contact.name,
                email=customer_invoice_contact.email,
                customer_name=customer.name,
                reference=customer.invoice_reference,
                address=customer.invoice_address,
            )
            return contact

        except ValidationError:
            self.log.append(msg)
            return None

    def get_contact_info(self, cost_center: str) -> InvoiceContact | None:
        """Return contact info for a customer."""

        msg = (
            f"Could not open/generate invoice. Contact information missing in database for "
            f"customer {self.customer_obj.internal_id}. See log files."
        )
        customer = self.get_customer_by_cost_center(cost_center=cost_center)
        customer_invoice_contact = self.get_customer_invoice_contact(customer=customer, msg=msg)
        return self.get_contact(
            customer_invoice_contact=customer_invoice_contact, customer=customer, msg=msg
        )

    def get_invoice_report(self, cost_center: str) -> dict | None:
        """Return invoice information as dictionary to generate Excel report."""

        records: list[dict] = []
        pooled_samples = []

        for raw_record in self.raw_records:
            if self.record_type == RecordType.Pool:
                pooled_samples += self.genologics_lims.samples_in_pools(
                    raw_record.name, raw_record.ticket
                )
            record = self.get_invoice_entity_record(
                cost_center=cost_center.lower(),
                discount=self.invoice_obj.discount,
                record=raw_record,
            )
            if record:
                records.append(record.dict())
            else:
                return None

        customer_obj = self.invoice_obj.customer
        contact = self.get_contact_info(cost_center)
        if not contact:
            return None

        try:
            invoice_report = InvoiceReport(
                cost_center=cost_center,
                project_number=getattr(customer_obj, f"project_account_{cost_center.lower()}"),
                customer_id=customer_obj.internal_id,
                customer_name=customer_obj.name,
                agreement=customer_obj.agreement_registration,
                invoice_id=self.invoice_obj.id,
                contact=contact.dict(),
                records=records,
                pooled_samples=pooled_samples,
                record_type=self.record_type,
            )
            return invoice_report.dict()
        except ValidationError:
            self.log.append("ValidationError in InvoiceReport class.")
            return None

    def _discount_price(self, record: Sample or Pool, discount: int = 0) -> int | None:
        """Return discount price for a sample or pool."""
        priority = self.get_priority(record, for_discount_price=True)
        full_price = getattr(record.application_version, f"price_{priority}")
        discount_factor = 1 - discount / 100
        return round(full_price * discount_factor) if full_price else 0

    def _cost_center_split_factor(
        self, price: int, cost_center: str, percent_kth: int, tag: str, version: str
    ) -> int | None:
        """Return split price based on cost center."""
        if price:
            try:
                if cost_center == CostCenters.kth:
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
            return 0
        return split_price

    def get_invoice_entity_record(
        self, cost_center: str, discount: int, record: Sample or Pool
    ) -> InvoiceInfo:
        """Return invoice information for a specific sample or pool."""
        application = self.get_application(record=record, discount=discount)
        split_discounted_price = self._cost_center_split_factor(
            price=application.discounted_price,
            cost_center=cost_center,
            percent_kth=application.percent_kth,
            tag=application.tag,
            version=application.version,
        )
        invoice_info = self.get_invoice_info(
            record=record,
            split_discounted_price=split_discounted_price,
            cost_center=cost_center,
            application=application,
        )

        return invoice_info

    def get_application(self, record: Sample or Pool, discount: int) -> InvoiceApplication | None:
        """Return the application information."""
        try:
            application = InvoiceApplication(
                tag=record.application_version.application.tag,
                version=record.application_version.version,
                percent_kth=record.application_version.application.percent_kth,
                discounted_price=self._discount_price(record, discount),
            )
            return application

        except ValidationError:
            self.log.append(f"Application tag/version seems to be missing for sample {record.id}.")

            return None

    def get_ticket(self, record: Sample or Pool) -> str:
        """Return ticket."""
        return record.ticket if self.record_type == RecordType.Pool else record.original_ticket

    def get_lims_id(self, record: Sample or Pool) -> str:
        """Return Lims id."""
        return None if self.record_type == RecordType.Pool else record.internal_id

    def get_priority(self, record: Sample or Pool, for_discount_price: bool = False) -> str:
        """Return the priority."""
        if self.customer_obj.internal_id == CustomerId.CUST032:
            priority = PriorityTerms.STANDARD
        elif self.record_type == RecordType.Pool or (
            record.priority_human == "clinical trials" and for_discount_price
        ):
            priority = PriorityTerms.RESEARCH
        else:
            priority = record.priority_human
        return priority

    def get_invoice_info(
        self, record, split_discounted_price: int, cost_center: str, application: InvoiceApplication
    ) -> InvoiceInfo:
        """Return the invoice_info to be used in the invoice report."""
        order = record.order
        ticket = self.get_ticket(record)
        lims_id = self.get_lims_id(record)
        priority = self.get_priority(record)
        price_kth: int = 0
        if cost_center == CostCenters.ki:
            price_kth: int = self._cost_center_split_factor(
                price=application.discounted_price,
                cost_center=CostCenters.kth,
                percent_kth=application.percent_kth,
                tag=application.tag,
                version=application.version,
            )

        try:
            invoice_info = InvoiceInfo(
                name=record.name,
                lims_id=lims_id,
                id=record.id,
                application_tag=record.application_version.application.tag,
                project=f"{order or 'NA'} ({ticket or 'NA'})",
                date=record.received_at.date() if record.received_at else "",
                price=split_discounted_price,
                priority=priority,
                price_kth=price_kth if cost_center == CostCenters.ki else None,
                total_price=application.discounted_price if cost_center == CostCenters.ki else None,
            )
            self.set_invoice_info(invoice_info=invoice_info)
            return invoice_info

        except ValidationError:
            self.log.append("ValidationError in InvoiceInfo class.")

    def set_invoice_info(self, invoice_info: InvoiceInfo):
        """Set invoice_info."""
        self.invoice_info = invoice_info

    def total_price(self) -> float | None:
        """Return the total price for all records in the invoice."""

        discount = self.invoice_obj.discount
        total_price = 0

        for record in self.raw_records:
            discount_price = self._discount_price(record, discount)
            if discount_price:
                total_price += discount_price
            else:
                return None
        return total_price
