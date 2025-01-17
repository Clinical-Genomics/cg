from pydantic import BaseModel


class OrderError(BaseModel):
    field: str
    message: str


class UserNotAssociatedWithCustomerError(OrderError):
    field: str = "customer"
    message: str = "User does not belong to customer"


class CustomerCannotSkipReceptionControlError(OrderError):
    field: str = "skip_reception_control"
    message: str = "Customer cannot skip reception control"


class CustomerDoesNotExistError(OrderError):
    field: str = "customer"
    message: str = "Customer does not exist"


class OrderNameRequiredError(OrderError):
    field: str = "name"
    message: str = "Order name is required"
