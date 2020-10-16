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


class AnalysisUploadError(CgError):
    """
    Error related to trying to upload analysis data.
    """


class CgDataError(CgError):
    """
    Error related to missing/incomplete data in Status DB
    """


class LimsDataError(CgError):
    """
    Error related to missing/incomplete data in LIMS
    """


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
    Exception raised when a bundle has already been added to Housekeeper
    """


class PipelineUnknownError(CgError):
    """
    Exception raised when a sample in a case has no data anlysis type
    """


class DeliveryReportError(CgError):
    """
    Exception related to delivery report creation
    """


class ValidationError(CgError):
    """
    Exception related to delivery report validation
    """


class MandatoryFilesMissing(CgError):
    """
    Exception raised when mandatory files are missing from the deliverables when storing an
    analysis in Housekeeper.
    """


class StoreError(CgError):
    """
    Exception related to storing an analysis
    """


class MipStartError(CgError):
    """
    Exception raised when MIP fails to start a run
    """


class PedigreeConfigError(CgError):
    """
    Raised when MIP pedigree config validation fails
    """

    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors


class TrailblazerAPIHTTPError(CgError):
    """Raised when Trailblazer REST API response code is not 200"""


class TrailblazerMissingAnalysisError(CgError):
    """Raised when Trailblazer REST API response code is not 200"""
