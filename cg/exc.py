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


class AnalysisNotReadyError(CgError):
    """
    Exception raised when some FASTQ file are missing when starting an analysis.
    """


class AnalysisNotCompletedError(CgError):
    """
    Exception raised when an analysis has not completed.
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


class SampleNotFoundError(CgDataError):
    """
    Exception raised when a sample is not found.
    """


class ChecksumFailedError(CgError):
    """
    Exception raised when the checksums of two files are not equal.
    """


class IlluminaCleanRunError(CgError):
    """
    Exception raised when the cleaning of an Illumina run failed.
    """


class DsmcAlreadyRunningError(CgError):
    """Raised when there is already a DCms process running on the system."""


class DecompressionNeededError(CgError):
    """Raised when decompression still needed to start analysis."""


class DeliveryReportError(CgError):
    """
    Exception related to delivery report creation.
    """


class DownsampleFailedError(CgError):
    """Exception related to downsampling of samples."""


class EmailNotSentError(CgError):
    """Raised when email not sent."""


class FlowCellError(CgError):
    """Raised when there is a problem with a flow cell."""


class IlluminaRunsNeededError(CgError):
    """Raised when fetching flow cells still needed to start analysis."""


class IlluminaRunEncryptionError(CgError):
    """Raised when there is a problem with encrypting a flow cell."""


class IlluminaRunAlreadyBackedUpError(CgError):
    """Raised when a flow cell is already backed-up."""


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


class HousekeeperArchiveMissingError(CgError):
    """
    Exception raised when an archive is missing in Housekeeper.
    """


class HousekeeperStoreError(CgError):
    """
    Exception raised when a deliverable file is malformed in Housekeeper.
    """


class LimsDataError(CgError):
    """
    Error related to missing/incomplete data in LIMS.
    """


class MicrosaltError(CgError):
    """
    Error related to Microsalt analysis.
    """


class MissingAnalysisRunDirectory(CgError):
    """
    Error related to missing analysis.
    """


class NfAnalysisError(CgError):
    """
    Error related to nf analysis.
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


class NfSampleSheetError(CgError):
    """Raised when something is wrong with the sample sheet."""


class SampleSheetContentError(CgError):
    """Raised when something is wrong with the sample sheet content."""


class SampleSheetFormatError(CgError):
    """Raised when something is wrong with the sample sheet format."""


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


class TrailblazerAnalysisNotFound(CgError):
    """Raised when a Trailblazer analysis is not found."""


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


class PdcError(CgError):
    """Exception raised when PDC API interaction errors."""


class PdcNoFilesMatchingSearchError(PdcError):
    """Exception raised when PDC API returns no files matching the search criteria."""


class DdnDataflowAuthenticationError(CgError):
    """Exception raised when the DDN Dataflow authentication fails."""


class DdnDataflowDeleteFileError(CgError):
    """Exception raised when the deletion via DDN Dataflow fails."""


class MissingFilesError(CgError):
    """Exception raised when there are missing files."""


class MetricsQCError(CgError):
    """Exception raised when QC metrics are not met."""


class MissingMetrics(CgError):
    """Exception raised when mandatory metrics are missing."""


class MissingSequencingMetricsError(CgError):
    """Exception raised when sequencing metrics are missing."""


class ArchiveJobFailedError(CgError):
    """Exception raised when an archival or retrieval job has failed."""


class XMLError(CgError):
    """Exception raised when something is wrong with the content of an XML file."""


class OrderNotFoundError(CgError):
    """Exception raised when an order is not found."""


class OrderExistsError(CgError):
    """Exception raised when cases and samples are added to a pre-existing order."""


class OrderMismatchError(CgError):
    """Exception raised when cases expected to belong to the same order are not part of the same order."""


class OrderNotDeliverableError(CgError):
    """Exception raised when no analysis is ready for delivery for an order."""


class DeliveryMessageNotSupportedError(CgError):
    """Exception raised when trying to fetch delivery messages for unsupported workflows."""


class OverrideCyclesError(CgError):
    """Exception raised when the override cycles are not correct."""


class Chanjo2APIClientError(CgError):
    """Exception related to the Chanjo2 API client."""


class Chanjo2RequestError(Chanjo2APIClientError):
    """Exception raised when a request to the Chanjo2 API client fails."""


class Chanjo2ResponseError(Chanjo2APIClientError):
    """Exception raised when the response from Chanjo2 API client fails validation."""
