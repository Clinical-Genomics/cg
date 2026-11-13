from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import read_yaml


def store_analysis_output(root_directory: Path, case_id: str, housekeeper_api: HousekeeperAPI):
    """Store analysis output in Housekeeper."""
    # TODO find a better location for the definition of this path
    case_deliverables_file = Path(root_directory, case_id, f"{case_id}_deliverables.yaml")
    case_deliverables: list[dict] = read_yaml(case_deliverables_file)

    existing_files = []
    missing_files = []
    for deliverable in case_deliverables:
        for file in deliverable["paths"]:
            if Path(file).is_file():
                file_data: dict = {
                    "path": file,
                    "file_type": deliverable["file_type"],
                    "tags": [deliverable["id"]],
                }
                existing_files.append(file_data)
            elif deliverable["mandatory"]:
                missing_files.append(file)

    if missing_files:
        raise MandatoryFileMissingError(f"Missing files: {missing_files}")

    housekeeper_api.add_bundle(bundle_data={"name": case_id, "files": existing_files})
    # TODO: Update analysis in StatusDB with housekeeper version
    # TODO:
