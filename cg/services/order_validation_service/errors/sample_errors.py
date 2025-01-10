from cg.services.order_validation_service.constants import MAXIMUM_VOLUME, MINIMUM_VOLUME
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


class WellPositionRmlMissingError(SampleError):
    field: str = "well_position_rml"
    message: str = "Well position is required for RML plates"


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


class WellFormatRmlError(SampleError):
    field: str = "well_position_rml"
    message: str = "Well position must follow the format A-H:1-12"


class ContainerNameMissingError(SampleError):
    field: str = "container_name"
    message: str = "Container must have a name"


class BufferInvalidError(SampleError):
    field: str = "elution_buffer"
    message: str = "Buffer must be Tris-HCl or Nuclease-free water when skipping reception control."


class ConcentrationRequiredError(SampleError):
    field: str = "concentration_ng_ul"
    message: str = "Concentration is required when skipping reception control."


class ConcentrationInvalidIfSkipRCError(SampleError):
    def __init__(self, sample_index: int, allowed_interval: tuple[float, float]):
        field: str = "concentration_ng_ul"
        message: str = (
            f"Concentration must be between {allowed_interval[0]} ng/μL and "
            f"{allowed_interval[1]} ng/μL if reception control should be skipped"
        )
        super(SampleError, self).__init__(sample_index=sample_index, field=field, message=message)


class PoolApplicationError(SampleError):
    def __init__(self, sample_index: int, pool_name: str):
        field: str = "application"
        message: str = f"Multiple applications detected in pool {pool_name}"
        super(SampleError, self).__init__(sample_index=sample_index, field=field, message=message)


class PoolPriorityError(SampleError):
    def __init__(self, sample_index: int, pool_name: str):
        field: str = "priority"
        message: str = f"Multiple priorities detected in pool {pool_name}"
        super(SampleError, self).__init__(sample_index=sample_index, field=field, message=message)
