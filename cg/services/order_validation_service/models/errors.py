from pydantic import BaseModel


class OrderValidationError(BaseModel):
    field: str
    message: str


class UserNotAssociatedWithCustomerError(OrderValidationError):
    field: str = "customer"
    message: str = "User does not belong to customer"


class TicketNumberRequiredError(OrderValidationError):
    field: str = "ticket_number"
    message: str = "Ticket number is required"


class CustomerCannotSkipReceptionControlError(OrderValidationError):
    field: str = "skip_reception_control"
    message: str = "Customer cannot skip reception control"


class CustomerDoesNotExistError(OrderValidationError):
    field: str = "customer"
    message: str = "Customer does not exist"


class OrderNameRequiredError(OrderValidationError):
    field: str = "name"
    message: str = "Order name is required"
