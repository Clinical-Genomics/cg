from cg.services.order_validation_service.errors.order_errors import OrderError


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


class MultipleSamplesError(CaseError):
    field: str = "samples"
    message: str = "Multiple samples in the same case not allowed"
