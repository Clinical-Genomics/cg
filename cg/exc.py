# -*- coding: utf-8 -*-


class CgError(Exception):

    def __init__(self, message):
        self.message = message


class AnalysisNotFinishedError(CgError):
    pass


class LimsDataError(CgError):
    pass


class MissingCustomerError(CgError):
    pass


class DuplicateRecordError(CgError):
    pass


class OrderFormError(CgError):
    pass


class OrderError(CgError):
    pass


class TicketCreationError(CgError):
    pass
