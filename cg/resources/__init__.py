from pathlib import Path

import pkg_resources

VALID_INDEXES_FILE: str = Path("resources", "20181012_Indices.csv").as_posix()

VALID_INDEXES_PATH: Path = Path(pkg_resources.resource_filename("cg", VALID_INDEXES_FILE))

RNAFUSION_BUNDLE_FILENAMES: str = Path("resources", "rnafusion_bundle_filenames.csv").as_posix()

RNAFUSION_BUNDLE_FILENAMES_PATH: Path = Path(
    pkg_resources.resource_filename("cg", RNAFUSION_BUNDLE_FILENAMES)
)
