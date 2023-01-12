"""
    Cg Exceptions.
"""


class CgError(Exception):

    """
    Base exception for the package.
    """

    def __init__(self, message: str = ""):
        super().__init__(message)


class AccessionNumerMissingError(CgError):
    """Raised when accession numers are not found in a gisaid cli log."""


class AnalysisDuplicationError(CgError):
    """
    Error related to trying to create analysis object that already exists in status-db.
    """


class AnalysisNotFinishedError(CgError):
    """
    Exception raised when an adding a MIP analysis to Housekeeper, but the analysis is not
    finished in MIP, as indicated in the qc sample info file.
    """


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
    Error related to missing/incomplete data in Status DB.
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


class FamilyLinkMissingError(CgError):
    """Raised when faimly link missing for a sample."""


class FastaSequenceMissingError(CgError):
    """
    Exception raised when expected sequence in fasta file is missing.
    """


class FlowCellError(CgError):
    """Raised when there is a problem with demultiplexing a flow cell."""


class FlowcellsNeededError(CgError):
    """Raised when fetching flowcells still needed to start analysis."""


class GisaidUploadFailedError(CgError):
    """Raised when gisaid upload fails."""


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


class InvalidFastaError(CgError):
    """
    Exception raised when fasta file content is invalid.
    """


class LimsDataError(CgError):
    """
    Error related to missing/incomplete data in LIMS.
    """


class MandatoryFilesMissing(CgError):
    """
    Exception raised when mandatory files are missing from the deliverables when storing an
    analysis in Housekeeper.
    """


class MipStartError(CgError):
    """
    Exception raised when MIP fails to start a run.
    """


class MultipleFamilyLinksError(CgError):
    """Raised when only one family was expected but more than one was found."""


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


class PipelineUnknownError(CgError):
    """
    Exception raised when a sample in a case has no data analysis type.
    """


class RnafusionStartError(CgError):
    """
    Exception raised when rnafusion fails to start
    """


class ScoutUploadError(CgError):
    """Raised when uploading to Scout fails."""


class StatinaAPIHTTPError(CgError):
    """Raised when Statina REST API response code is not 200."""


class StoreError(CgError):
    """
    Exception related to storing an analysis.
    """


class TicketCreationError(CgError):
    """
    Exception related to ticket creation.
    """


class TrailblazerAPIHTTPError(CgError):
    """Raised when Trailblazer REST API response code is not 200."""


class TrailblazerMissingAnalysisError(CgError):
    """Raised when Trailblazer REST API response code is not 200."""


class ValidationError(CgError):
    """
    Exception related to delivery report validation.
    """


class DeleteDemuxError(CgError):
    """Raised when there is an issue with wiping a flowcell before start."""


class CustomerPermissionError(CgError):
    """Exception related to the limited permissions of a customer."""


class DataIntegrityError(CgError):
    """Raised when data integrity is not met."""


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
