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


class FlowcellError(CgError):
    """Raised when there is a problem with demultiplexing a flowcell"""


class DecompressionNeededError(CgError):
    """Raised when decompression still needed to start analysis"""


class FlowcellsNeededError(CgError):
    """Raised when fetching flowcells still needed to start analysis"""


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
    Exception raised when a sample in a case has no data analysis type
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


class HousekeeperVersionMissingError(CgError):
    """
    Exception raised when family version is missing in Housekeeper.
    """


class HousekeeperFileMissingError(CgError):
    """
    Exception raised when a file is missing in Housekeeper.
    """

    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors


class FastaSequenceMissingError(CgError):
    """
    Exception raised when expected sequence in fasta file is missing.
    """


class InvalidFastaError(CgError):
    """
    Exception raised when fasta file content is invalid.
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


class MultipleFamilyLinksError(CgError):
    """Raised when only one family was expected but more than one was found"""


class FamilyLinkMissingError(CgError):
    """Raised when faimly link missing for a sample"""


class AccessionNumerMissingError(CgError):
    """Raised when accession numers are not found in a gisaid cli log"""


class EmailNotSentError(CgError):
    """Raised when email not sent"""


class GisaidUploadFailedError(CgError):
    """Raised when gisaid upload fails"""


class StatinaAPIHTTPError(CgError):
    """Raised when Statina REST API response code is not 200"""
