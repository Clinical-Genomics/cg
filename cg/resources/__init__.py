from pathlib import Path

import pkg_resources

valid_indexes_file: str = Path("resources", "20181012_Indices.csv").as_posix()

valid_indexes_path: Path = Path(pkg_resources.resource_filename("cg", valid_indexes_file))

rnafusion_bundle_filenames: str = Path("resources", "rnafusion_bundle_filenames.csv").as_posix()

rnafusion_bundle_filenames_path: Path = Path(
    pkg_resources.resource_filename("cg", rnafusion_bundle_filenames)
)
