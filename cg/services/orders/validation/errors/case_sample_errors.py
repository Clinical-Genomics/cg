from cg.services.orders.validation.constants import MAXIMUM_VOLUME, MINIMUM_VOLUME
from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.sample_errors import SampleError


class CaseSampleError(CaseError, SampleError):
    pass


class OccupiedWellError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well is already occupied"


class ApplicationArchivedError(CaseSampleError):
    field: str = "application"
    message: str = "Chosen application is archived"


class ApplicationNotValidError(CaseSampleError):
    field: str = "application"
    message: str = "Chosen application does not exist"


class ApplicationNotCompatibleError(CaseSampleError):
    field: str = "application"
    message: str = "Application is not allowed for the chosen workflow"


class SampleNameRepeatedError(CaseSampleError):
    field: str = "name"
    message: str = "Sample name already used"


class SampleNameSameAsCaseNameError(CaseSampleError):
    field: str = "name"
    message: str = "Sample name can not be the same as any case name in order"


class InvalidFatherSexError(CaseSampleError):
    field: str = "father"
    message: str = "Father must be male"


class FatherNotInCaseError(CaseSampleError):
    field: str = "father"
    message: str = "Father must be in the same case"


class InvalidMotherSexError(CaseSampleError):
    field: str = "mother"
    message: str = "Mother must be female"


class PedigreeError(CaseSampleError):
    message: str = "Invalid pedigree relationship"


class DescendantAsMotherError(PedigreeError):
    field: str = "mother"
    message: str = "Descendant sample cannot be mother"


class DescendantAsFatherError(PedigreeError):
    field: str = "father"
    message: str = "Descendant sample cannot be father"


class SampleIsOwnMotherError(PedigreeError):
    field: str = "mother"
    message: str = "Sample cannot be its own mother"


class SampleIsOwnFatherError(PedigreeError):
    field: str = "father"
    message: str = "Sample cannot be its own father"


class MotherNotInCaseError(CaseSampleError):
    field: str = "mother"
    message: str = "Mother must be in the same case"


class SampleDoesNotExistError(CaseSampleError):
    field: str = "internal_id"
    message: str = "The sample does not exist"


class SubjectIdSameAsCaseNameError(CaseSampleError):
    field: str = "subject_id"
    message: str = "Subject id must be different from the case name"


class ConcentrationRequiredIfSkipRCError(CaseSampleError):
    field: str = "concentration_ng_ul"
    message: str = "Concentration is required when skipping reception control"


class SubjectIdSameAsSampleNameError(CaseSampleError):
    field: str = "subject_id"
    message: str = "Subject id must be different from the sample name"


class InvalidConcentrationIfSkipRCError(CaseSampleError):
    def __init__(self, case_index: int, sample_index: int, allowed_interval: tuple[float, float]):
        field: str = "concentration_ng_ul"
        message: str = (
            f"Concentration must be between {allowed_interval[0]} ng/μL and {allowed_interval[1]} ng/μL if reception control should be skipped"
        )
        super(CaseSampleError, self).__init__(
            case_index=case_index, sample_index=sample_index, field=field, message=message
        )


class WellPositionMissingError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well position is required for well plates"


class ContainerNameMissingError(CaseSampleError):
    field: str = "container_name"
    message: str = "Container name is required for well plates"


class InvalidVolumeError(CaseSampleError):
    field: str = "volume"
    message: str = f"Volume must be between {MINIMUM_VOLUME}-{MAXIMUM_VOLUME} μL"


class VolumeRequiredError(CaseSampleError):
    field: str = "volume"
    message: str = "Volume is required"


class InvalidBufferError(CaseSampleError):
    field: str = "elution_buffer"
    message: str = "The chosen buffer is not allowed when skipping reception control"


class SexSubjectIdError(CaseSampleError):
    field: str = "sex"
    message: str = "Another sample with the same subject id has a different sex"


class CaptureKitResetError(CaseSampleError):
    field: str = "warnings"
    message: str = "No bait set will be used, since it is not required for this application."


class CaptureKitMissingError(CaseSampleError):
    field: str = "capture_kit"
    message: str = "Bait set is required for TGS analyses"


class InvalidCaptureKitError(CaseSampleError):
    field: str = "capture_kit"
    message: str = "Bait set must be valid"


class WellFormatError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well position must follow the format A-H:1-12"


class ContainerNameRepeatedError(CaseSampleError):
    field: str = "container_name"
    message: str = "Tube names must be unique among samples"


class StatusUnknownError(CaseSampleError):
    field: str = "status"
    message: str = "Samples in case cannot all have status unknown"


class BufferMissingError(CaseSampleError):
    field: str = "elution_buffer"
    message: str = "Buffer must be specified with this application"


class SampleOutsideOfCollaborationError(CaseSampleError):
    field: str = "internal_id"
    message: str = "Sample cannot be outside of collaboration"


class ExistingSampleWrongTypeError(CaseSampleError):
    field: str = "internal_id"
    message: str = "The sample is not compatible with the order type."


class SampleNameAlreadyExistsError(CaseSampleError):
    field: str = "name"
    message: str = "Sample name already exists in a previous order"
