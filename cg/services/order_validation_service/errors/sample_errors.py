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

   
class SampleDoesNotExistError(SampleError):
    field: str = "internal_id"
    message: str = "The sample does not exist"
