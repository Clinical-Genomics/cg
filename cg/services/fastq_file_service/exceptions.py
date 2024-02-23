class FastqServiceError(Exception):
    pass


class ConcatenationError(FastqServiceError):
    pass


class InvalidFastqDirectory(FastqServiceError):
    pass
