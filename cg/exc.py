# -*- coding: utf-8 -*-
"""
    Cg Exceptions
"""


class CgError(Exception):

    """
        Base exception for the package
    """

    def __init__(self, message):
        super(CgError, self).__init__()
        self.message = message


class AnalysisNotFinishedError(CgError):
    """
        Exception raised when an adding a MIP analysis to Housekeeper, but the analysis is not
        finished in MIP, as indicated in the qc sample info file.

    """


class AnalysisDuplicationError(CgError):
    """
        Error related to trying to create analysis object that already exists in status-db.
    """


class LimsDataError(CgError):
    """
        Error related to missing/incomplete data in LIMS
    """


# class MissingCustomerError(CgError):
#     """
#         Exception related to missing customer
#     """


class DuplicateRecordError(CgError):
    """
        Exception related to duplicate records in LoqusDB.
    """


class DuplicateSampleError(CgError):
    """
        Exception raised when sample duplicate is found in loqusdb
    """


class CaseNotFoundError(CgError):
    """
        Exception raised when a case is not found in loqusdb
    """


class OrderFormError(CgError):
    """
        Exception related to the order form
    """


class OrderError(CgError):
    """
        Exception related to orders
    """


class TicketCreationError(CgError):
    """
        Exception related to ticket creation
    """


class BalsamicStartError(CgError):
    """
        Exception raised when Balsamic fails to start
    """


class BundleAlreadyAddedError(CgError):
    """
        Exception rasied when a bundle has already been added to Housekeeper
    """
