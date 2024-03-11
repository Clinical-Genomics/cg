"""Error handling for the janus api."""


class JanusAPIError(Exception):
    def __init__(self, message: str = ""):
        super(JanusAPIError, self).__init__()
        self.message = message


class JanusClientError(JanusAPIError):
    """Raises an error in case of an error when parsing a JSON file."""


class JanusServerError(JanusAPIError):
    """Raises an error in case of an error when parsing a JSON file."""
