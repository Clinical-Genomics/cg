# -*- coding: utf-8 -*-


class CgError(Exception):

    """Base exception for the package."""

    def __init__(self, message):
        super(CgError, self).__init__()
        self.message = message


class AnalysisNotFinishedError(CgError):
    pass


class AnalysisDuplicationError(CgError):
    """Error related to trying to create duplicate analysis objects"""


class LimsDataError(CgError):
    """Error related to missing/incomplete data in LIMS."""
    pass


class MissingCustomerError(CgError):
    pass


class DuplicateRecordError(CgError):
    pass


class DuplicateSampleError(CgError):
    """
        Exception raised when sample duplicate is found in loqusdb
    """


class CaseNotFoundError(CgError):
    """
        Exception raised when a case is not found in loqusdb
    """


class OrderFormError(CgError):
    pass


class OrderError(CgError):
    pass


class TicketCreationError(CgError):
    pass
