"""
    Cg Exceptions.
"""


class CgError(Exception):

    """
    Base exception for the package.
    """

    def __init__(self, message: str = ""):
        super().__init__(message)


class AnalysisUploadError(CgError):
    """
    Error related to trying to upload analysis data.
    """


class AnalysisAlreadyUploadedError(CgError):
    """
    Error related to trying to upload an already (or in the process) uploaded analysis.
    """


class BalsamicStartError(CgError):
    """
    Exception raised when Balsamic fails to start.
    """


class BundleAlreadyAddedError(CgError):
    """
    Exception raised when a bundle has already been added to Housekeeper.
    """


class CaseNotFoundError(CgError):
    """
    Exception raised when a case is not found.
    """


class CgDataError(CgError):
    """
    Error related to missing or incomplete data in Status DB.
    """


class ChecksumFailedError(CgError):
    """
    Exception raised when the checksums of two files are not equal.
    """


class DecompressionNeededError(CgError):
    """Raised when decompression still needed to start analysis."""


class DeliveryReportError(CgError):
    """
    Exception related to delivery report creation.
    """


class EmailNotSentError(CgError):
    """Raised when email not sent."""


class FlowCellError(CgError):
    """Raised when there is a problem with demultiplexing a flow cell."""


class FlowCellsNeededError(CgError):
    """Raised when fetching flow cells still needed to start analysis."""


class HousekeeperFileMissingError(CgError):
    """
    Exception raised when a file is missing in Housekeeper.
    """

    def __init__(self, message: str = "", errors=None):
        super().__init__(message)
        self.errors = errors


class HousekeeperBundleVersionMissingError(CgError):
    """
    Exception raised when bundle version is missing in Housekeeper.
    """


class LimsDataError(CgError):
    """
    Error related to missing/incomplete data in LIMS.
    """


class OrderError(CgError):
    """
    Exception related to orders.
    """


class OrderFormError(CgError):
    """
    Exception related to the order form.
    """


class PedigreeConfigError(CgError):
    """
    Raised when MIP pedigree config validation fails.
    """

    def __init__(self, message: str = "", errors=None):
        super().__init__(message)
        self.errors = errors


class RunParametersError(CgError):
    """Raised when something is wrong with the run parameters file."""


class SampleSheetError(CgError):
    """Raised when something is wrong with the sample sheet."""


class ScoutUploadError(CgError):
    """Raised when uploading to Scout fails."""


class StatinaAPIHTTPError(CgError):
    """Raised when Statina REST API response code is not 200."""


class TicketCreationError(CgError):
    """
    Exception related to ticket creation.
    """


class TrailblazerAPIHTTPError(CgError):
    """Raised when Trailblazer REST API response code is not 200."""


class ValidationError(CgError):
    """
    Exception related to delivery report validation.
    """


class DeleteDemuxError(CgError):
    """Raised when there is an issue with wiping a flowcell before start."""


class LoqusdbError(CgError):
    """Exception related to the Loqusdb app."""


class LoqusdbUploadCaseError(LoqusdbError):
    """Exception raised when a case could not be uploaded to Loqusdb."""


class LoqusdbDeleteCaseError(LoqusdbError):
    """Exception raised when a case cannot be deleted from Loqusdb."""


class LoqusdbDuplicateRecordError(LoqusdbError):
    """Exception related to duplicate records in Loqusdb."""


class PdcNoFilesMatchingSearchError(CgError):
    """Exception raised when PDC API returns no files matching the search criteria."""


class DdnDataflowAuthenticationError(CgError):
    """Exception raised when the DDN Dataflow authentication fails."""


class MissingFilesError(CgError):
    """Exception raised when there are missing files."""


class MetricsQCError(CgError):
    """Exception raised when QC metrics are not met."""


class MissingMetrics(CgError):
    """Exception raised when mandatory metrics are missing."""
