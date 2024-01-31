"""Constants specific for Tar extraction"""

from cg.utils.enums import ListEnum


class FlowCellExtractionParameters(ListEnum):
    EXTRACT_FILE: list = [
        "-xf",
    ]
    EXCLUDE_FILES: list = [
        "--exclude=RTAComplete.txt",
        "--exclude=demuxstarted.txt",
        "--exclude=Thumbnail_Images",
    ]
    CHANGE_TO_DIR: list = [
        "-C",
    ]
