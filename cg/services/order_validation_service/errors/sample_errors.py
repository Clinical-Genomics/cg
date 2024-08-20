from cg.services.order_validation_service.errors.order_errors import OrderError


class SampleError(OrderError):
    sample_index: int


class ApplicationNotValidError(SampleError):
    field: str = "application"
    message: str = "Chosen application does not exist"


class ApplicationNotCompatibleError(SampleError):
    field: str = "application"
    message: str = "Chosen application is not compatible with workflow"
