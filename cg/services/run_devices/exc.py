from cg.exc import CgError


class PostProcessingRunFileManagerError(CgError):
    """Error raised if something goes wrong managing the sequencing run files."""

    pass


class PostProcessingRunDataGeneratorError(CgError):
    """Error raised if something goes wrong parsing the run directory data."""

    pass


class PostProcessingParsingError(CgError):
    """Error raised if something goes wrong parsing the sequencing run metrics."""

    pass


class PostProcessingDataTransferError(CgError):
    """Error raised if something goes wrong creating the DTOs for post-processing."""

    pass


class PostProcessingStoreDataError(CgError):
    """Error raised if something goes wrong storing the post-processing data in StatusDB."""

    pass


class PostProcessingStoreFileError(CgError):
    """Error raised if something goes wrong storing the post-processing files in Housekeeper."""

    pass


class PostProcessingError(CgError):
    """Error raised if something goes wrong during post-processing."""

    pass
