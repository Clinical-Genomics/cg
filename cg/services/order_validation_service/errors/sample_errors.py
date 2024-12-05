from cg.services.order_validation_service.constants import (
    MAXIMUM_VOLUME,
    MINIMUM_VOLUME,
)
from cg.services.order_validation_service.errors.order_errors import OrderError


class SampleError(OrderError):
    sample_index: int


class ApplicationNotValidError(SampleError):
    field: str = "application"
    message: str = "Chosen application does not exist"


class ApplicationArchivedError(SampleError):
    field: str = "application"
    message: str = "Chosen application is archived"


class ApplicationNotCompatibleError(SampleError):
    field: str = "application"
    message: str = "Chosen application is not compatible with workflow"


class OccupiedWellError(SampleError):
    field: str = "well_position"
    message: str = "Well is already occupied"


class WellPositionMissingError(SampleError):
    field: str = "well_position"
    message: str = "Well position is required for well plates"


class SampleNameRepeatedError(SampleError):
    field: str = "name"
    message: str = "Sample name repeated"


class InvalidVolumeError(SampleError):
    field: str = "volume"
    message: str = f"Volume must be between {MINIMUM_VOLUME}-{MAXIMUM_VOLUME} μL"


class VolumeRequiredError(SampleError):
    field: str = "volume"
    message: str = "Volume is required"


class OrganismDoesNotExistError(SampleError):
    field: str = "organism"
    message: str = "Organism does not exist"


class SampleNameNotAvailableError(SampleError):
    field: str = "name"
    message: str = "Sample name already used in previous order"


class ContainerNameRepeatedError(SampleError):
    field: str = "container_name"
    message: str = "Tube names must be unique among samples"


class WellFormatError(SampleError):
    field: str = "well_position"
    message: str = "Well position must follow the format A-H:1-12"


class ContainerNameMissingError(SampleError):
    field: str = "container_name"
    message: str = "Container must have a name"
