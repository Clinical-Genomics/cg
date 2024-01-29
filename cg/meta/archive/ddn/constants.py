from enum import StrEnum

OSTYPE: str = "Unix/MacOS"
ROOT_TO_TRIM: str = "/home"

DESTINATION_ATTRIBUTE: str = "destination"
SOURCE_ATTRIBUTE: str = "source"

DELETE_FILE_SUCCESSFUL_MESSAGE: str = "Object has been deleted"


class DataflowEndpoints(StrEnum):
    """Enum containing all DDN dataflow endpoints used."""

    ARCHIVE_FILES = "files/archive"
    DELETE_FILE = "files/delete"
    GET_AUTH_TOKEN = "auth/token"
    REFRESH_AUTH_TOKEN = "auth/token/refresh"
    RETRIEVE_FILES = "files/retrieve"
    GET_JOB_STATUS = "activity/jobs/"


class JobStatus(StrEnum):
    """Enum for the different job statuses which can be returned via Miria."""

    CANCELED = "Canceled"
    COMPLETED = "Completed"
    DENIED = "Denied"
    CREATION_IN_PROGRESS = "Creation in progress"
    IN_QUEUE = "In Queue"
    INVALID_LICENSE = "Invalid license"
    ON_VALIDATION = "On validation"
    REFUSED = "Refused"
    RUNNING = "Running"
    SUSPENDED = "Suspended"
    TERMINATED_ON_ERROR = "Terminated on error"
    TERMINATED_ON_WARNING = "Terminated on warning"


FAILED_JOB_STATUSES: list[str] = [
    JobStatus.CANCELED,
    JobStatus.DENIED,
    JobStatus.INVALID_LICENSE,
    JobStatus.REFUSED,
    JobStatus.TERMINATED_ON_ERROR,
    JobStatus.TERMINATED_ON_WARNING,
]
ONGOING_JOB_STATUSES: list[str] = [
    JobStatus.CREATION_IN_PROGRESS,
    JobStatus.IN_QUEUE,
    JobStatus.ON_VALIDATION,
    JobStatus.RUNNING,
]

METADATA_LIST = "metadataList"


class MetadataFields(StrEnum):
    CUSTOMER_NAME: str = "customer_name"
    PREP_CATEGORY: str = "prep_category"
    SAMPLE_NAME: str = "sample_name"
    SEQUENCED_AT: str = "sequenced_at"
    TICKET_NUMBER: str = "ticket_number"
    NAME = "metadataName"
    VALUE = "value"
