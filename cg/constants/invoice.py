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
    costcenter: str = "costcenter"
    project_number: str = "project_number"
    customer_id: str = "customer_id"
    customer_name: str = "customer_name"
    agreement: str = "agreement"
    invoice_id: str = "invoice_id"
    contact: str = "contact"
    records: str = "records"
    pooled_samples: str = "pooled_samples"
    record_type: str = "record_type"
