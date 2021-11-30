"""
    Cg Exceptions
"""


class CgError(Exception):

    """
    Base exception for the package
    """

    def __init__(self, message: str = ""):
        super(CgError, self).__init__()
        self.message = message


class AccessionNumerMissingError(CgError):
    """Raised when accession numers are not found in a gisaid cli log"""


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


class BalsamicStartError(CgError):
    """
    Exception raised when Balsamic fails to start
    """


class BundleAlreadyAddedError(CgError):
    """
    Exception raised when a bundle has already been added to Housekeeper
    """


class CaseNotFoundError(CgError):
    """
    Exception raised when a case is not found in loqusdb
    """


class CgDataError(CgError):
    """
    Error related to missing/incomplete data in Status DB
    """


class DecompressionNeededError(CgError):
    """Raised when decompression still needed to start analysis"""


class DeliveryReportError(CgError):
    """
    Exception related to delivery report creation
    """


class DuplicateRecordError(CgError):
    """
    Exception related to duplicate records in LoqusDB.
    """


class DuplicateSampleError(CgError):
    """
    Exception raised when sample duplicate is found in loqusdb
    """


class EmailNotSentError(CgError):
    """Raised when email not sent"""


class FamilyLinkMissingError(CgError):
    """Raised when faimly link missing for a sample"""


class FastaSequenceMissingError(CgError):
    """
    Exception raised when expected sequence in fasta file is missing.
    """


class FlowcellError(CgError):
    """Raised when there is a problem with demultiplexing a flowcell"""


class FlowcellsNeededError(CgError):
    """Raised when fetching flowcells still needed to start analysis"""


class GisaidUploadFailedError(CgError):
    """Raised when gisaid upload fails"""


class HousekeeperFileMissingError(CgError):
    """
    Exception raised when a file is missing in Housekeeper.
    """

    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors


class HousekeeperVersionMissingError(CgError):
    """
    Exception raised when family version is missing in Housekeeper.
    """


class InvalidFastaError(CgError):
    """
    Exception raised when fasta file content is invalid.
    """


class LimsDataError(CgError):
    """
    Error related to missing/incomplete data in LIMS
    """


class MandatoryFilesMissing(CgError):
    """
    Exception raised when mandatory files are missing from the deliverables when storing an
    analysis in Housekeeper.
    """


class MipStartError(CgError):
    """
    Exception raised when MIP fails to start a run
    """


class MultipleFamilyLinksError(CgError):
    """Raised when only one family was expected but more than one was found"""


class OrderError(CgError):
    """
    Exception related to orders
    """


class OrderFormError(CgError):
    """
    Exception related to the order form
    """


class PedigreeConfigError(CgError):
    """
    Raised when MIP pedigree config validation fails
    """

    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors


class PipelineUnknownError(CgError):
    """
    Exception raised when a sample in a case has no data analysis type
    """


class ScoutUploadError(CgError):
    """Raised when uploading to Scout fails"""


class StatinaAPIHTTPError(CgError):
    """Raised when Statina REST API response code is not 200"""


class StoreError(CgError):
    """
    Exception related to storing an analysis
    """


class TicketCreationError(CgError):
    """
    Exception related to ticket creation
    """


class TrailblazerAPIHTTPError(CgError):
    """Raised when Trailblazer REST API response code is not 200"""


class TrailblazerMissingAnalysisError(CgError):
    """Raised when Trailblazer REST API response code is not 200"""


class ValidationError(CgError):
    """
    Exception related to delivery report validation
    """
