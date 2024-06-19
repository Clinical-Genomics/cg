from pathlib import Path

import pkg_resources

from cg.constants import FileExtensions

RAREDISEASE_BUNDLE_FILENAMES: str = (
    Path("resources", "raredisease_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)

RNAFUSION_BUNDLE_FILENAMES: str = (
    Path("resources", "rnafusion_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)

TAXPROFILER_BUNDLE_FILENAMES: str = (
    Path("resources", "taxprofiler_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)

TOMTE_BUNDLE_FILENAMES: str = (
    Path("resources", "tomte_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)

RAREDISEASE_BUNDLE_FILENAMES_PATH = Path(
    pkg_resources.resource_filename("cg", RAREDISEASE_BUNDLE_FILENAMES)
)

RNAFUSION_BUNDLE_FILENAMES_PATH: Path = Path(
    pkg_resources.resource_filename("cg", RNAFUSION_BUNDLE_FILENAMES)
)

TAXPROFILER_BUNDLE_FILENAMES_PATH: Path = Path(
    pkg_resources.resource_filename("cg", TAXPROFILER_BUNDLE_FILENAMES)
)

TOMTE_BUNDLE_FILENAMES_PATH: Path = Path(
    pkg_resources.resource_filename("cg", TOMTE_BUNDLE_FILENAMES)
)
