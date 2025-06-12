from cg.services.orders.validation.errors.order_errors import OrderError


class CaseError(OrderError):
    case_index: int


class RepeatedCaseNameError(CaseError):
    field: str = "name"
    message: str = "Case name already used"


class InvalidGenePanelsError(CaseError):
    def __init__(self, case_index: int, panels: list[str]):
        message = "Invalid panels: " + ",".join(panels)
        super(CaseError, self).__init__(field="panels", case_index=case_index, message=message)


class RepeatedGenePanelsError(CaseError):
    field: str = "panels"
    message: str = "Gene panels must be unique"


class CaseNameNotAvailableError(CaseError):
    field: str = "name"
    message: str = "Case name already used in a previous order"


class CaseDoesNotExistError(CaseError):
    field: str = "internal_id"
    message: str = "The case does not exist"


class CaseOutsideOfCollaborationError(CaseError):
    field: str = "internal_id"
    message: str = "Case does not belong to collaboration"


class MultipleSamplesInCaseError(CaseError):
    field: str = "sample_errors"
    message: str = "Multiple samples in the same case not allowed"


class MoreThanTwoSamplesInCaseError(CaseError):
    field: str = "sample_errors"
    message: str = "More than two samples in the same case not allowed"


class NumberOfNormalSamplesError(CaseError):
    field: str = "sample_errors"


class DoubleNormalError(NumberOfNormalSamplesError):
    message: str = "Only one non-tumour sample is allowed per case"


class DoubleTumourError(NumberOfNormalSamplesError):
    message: str = "Only one tumour sample is allowed per case"


class NormalOnlyWGSError(NumberOfNormalSamplesError):
    message: str = "It is not possible to run the analysis on only one normal WGS sample."


class NewCaseWithoutAffectedSampleError(CaseError):
    field: str = "sample_errors"
    message: str = "Each case needs at least one affected sample"


class ExistingCaseWithoutAffectedSampleError(CaseError):
    field: str = "sample_errors"
    message: str = (
        "This case contains no affected sample. Please create a new case with at least one affected sample."
    )


class MultiplePrepCategoriesError(CaseError):
    field: str = "sample_errors"
    message: str = "Case cannot contain samples with incompatible applications"
