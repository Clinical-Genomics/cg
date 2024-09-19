from cg.exc import CgError


class SampleSheetError(CgError):
    """Parent class for all sample sheet exceptions."""

    pass


class SampleSheetWrongFormatError(SampleSheetError):
    """Raised when the sample sheet is in the wrong format."""

    pass


class SampleSheetValidationError(SampleSheetError):
    """Raised when the sample sheet content is invalid."""

    pass
