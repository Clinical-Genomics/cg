from pathlib import Path

from cg.constants import FileExtensions
from cg.utils.files import get_project_root_dir

project_root_dir: Path = get_project_root_dir()

NALLO_BUNDLE_FILENAMES: str = (
    Path("resources", "nallo_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)
NALLO_BUNDLE_FILENAMES_PATH = Path(project_root_dir, NALLO_BUNDLE_FILENAMES)

RAREDISEASE_BUNDLE_FILENAMES: str = (
    Path("resources", "raredisease_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)
RAREDISEASE_BUNDLE_FILENAMES_PATH = Path(project_root_dir, RAREDISEASE_BUNDLE_FILENAMES)

RNAFUSION_BUNDLE_FILENAMES: str = (
    Path("resources", "rnafusion_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)
RNAFUSION_BUNDLE_FILENAMES_PATH = Path(project_root_dir, RNAFUSION_BUNDLE_FILENAMES)

TAXPROFILER_BUNDLE_FILENAMES: str = (
    Path("resources", "taxprofiler_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)
TAXPROFILER_BUNDLE_FILENAMES_PATH = Path(project_root_dir, TAXPROFILER_BUNDLE_FILENAMES)

TOMTE_BUNDLE_FILENAMES: str = (
    Path("resources", "tomte_bundle_filenames").with_suffix(FileExtensions.YAML).as_posix()
)
TOMTE_BUNDLE_FILENAMES_PATH = Path(project_root_dir, TOMTE_BUNDLE_FILENAMES)
