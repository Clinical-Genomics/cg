from pathlib import Path

import pkg_resources

valid_indexes_file = "resources/20181012_Indices.csv"

valid_indexes_path = Path(pkg_resources.resource_filename("cg", valid_indexes_file))
