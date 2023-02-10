from cg.utils.enums import StrEnum


class ContactInvoice(StrEnum):
    name: str = "name"
    email: str = "email"
    customer_name: str = "customer_name"
    reference: str = "reference"
    address: str = "address"
