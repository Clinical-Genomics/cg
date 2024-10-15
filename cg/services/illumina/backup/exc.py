from cg.exc import CgError


class DsmcMissingSequenceFileError(CgError):
    """Exception raised when a Dsmc sequence file is not found."""


class DsmcMissingEncryptionKeyError(CgError):
    """Exception raised when a Dsmc encryption key is not found."""
