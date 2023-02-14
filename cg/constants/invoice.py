from cg.utils.enums import StrEnum


class InvoiceInfo(StrEnum):
    name: str = "name"
    lims_id: str = "lims_id"
    id: str = "id"
    application_tag: str = "application_tag"
    project: str = "project"
    date: str = "date"
    price: str = "price"
    priority: str = "priority"
    price_kth: str = "price_kth"
    total_price: str = "total_price"


class Prepare(StrEnum):
    cost_center: str = "cost_center"
    project_number: str = "project_number"
    customer_id: str = "customer_id"
    customer_name: str = "customer_name"
    agreement: str = "agreement"
    invoice_id: str = "invoice_id"
    contact: str = "contact"
    records: str = "records"
    pooled_samples: str = "pooled_samples"
    record_type: str = "record_type"


class CustomerNames(StrEnum):
    cust999: str = "cust999"
    cust032: str = "cust032"
    cust001: str = "cust001"
    cust132: str = "cust132"


class Costcenters(StrEnum):
    ki: str = "ki"
    kth: str = "kth"


class ContactInvoice(StrEnum):
    name: str = "name"
    email: str = "email"
    customer_name: str = "customer_name"
    reference: str = "reference"
    address: str = "address"


class ApplicationInfo(StrEnum):
    version: str = "version"
    tag: str = "tag"
    discounted_price: str = "discounted_price"
    percent_kth: str = "percent_kth"
