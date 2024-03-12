class ArnoldAPIError(Exception):
    def __init__(self, message: str = ""):
        super(ArnoldAPIError, self).__init__()
        self.message = message


class ArnoldClientError(ArnoldAPIError):
    """Raises an error in case of an error when parsing a JSON file."""


class ArnoldServerError(ArnoldAPIError):
    """Raises an error in case of an error when parsing a JSON file."""
