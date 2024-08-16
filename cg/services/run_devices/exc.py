from cg.exc import CgError


class PostProcessingRunFileManagerError(CgError):
    pass


class PostProcessingRunDataGeneratorError(CgError):
    pass


class PostProcessingParsingError(CgError):
    pass


class PostProcessingDataTransferError(CgError):
    pass


class PostProcessingStoreDataError(CgError):
    pass


class PostProcessingStoreFileError(CgError):
    pass


class PostProcessingError(CgError):
    pass
