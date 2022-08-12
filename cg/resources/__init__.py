from pathlib import Path

import pkg_resources

valid_indexes_file = "resources/20181012_Indices.csv"

valid_indexes_path = Path(pkg_resources.resource_filename("cg", valid_indexes_file))

rnafusion_bundle_filenames = "resources/rnafusion_bundle_filenames.csv"

rnafusion_bundle_filenames_path = Path(
    pkg_resources.resource_filename("cg", rnafusion_bundle_filenames)
)
