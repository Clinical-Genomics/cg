class OrderServiceError(Exception):
    pass


class OrderNotFoundError(OrderServiceError):
    pass
