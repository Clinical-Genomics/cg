from cg.services.order_validation_service.errors.order_errors import OrderError


class SampleError(OrderError):
    sample_index: int
