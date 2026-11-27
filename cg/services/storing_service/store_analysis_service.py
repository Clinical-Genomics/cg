from datetime import datetime
from pathlib import Path
from typing import cast

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.io.yaml import read_yaml
from cg.store.models import Analysis
from cg.store.store import Store


def store_analysis_output(
    analysis_id: int, root_directory: Path, housekeeper_api: HousekeeperAPI, status_db: Store
):
    """Store analysis output in Housekeeper.
    :param analysis_id:
    :param status_db:
    """
    analysis: Analysis = status_db.get_analysis_by_entry_id_strict(analysis_id)
    case_id: str = analysis.case_internal_id

    case_deliverables: list[dict] = read_yaml(analysis.case.get_deliverables_file(root_directory))

    existing_files: list[dict] = []
    for deliverable in case_deliverables:
        for file in deliverable["paths"]:
            if Path(file).is_file():
                file_data: dict = {
                    "path": file,
                    "file_type": deliverable["file_type"],
                    "tags": [deliverable["id"]],
                    "archive": False,
                }
                existing_files.append(file_data)

    bundle, version = housekeeper_api.add_bundle(
        bundle_data={"name": case_id, "files": existing_files, "created_at": datetime.now()}
    )
    housekeeper_api.include(version)
    housekeeper_api.add_commit(bundle)
    status_db.update_analysis_housekeeper_version_id(
        analysis_id=analysis_id, version_id=cast(int, version.id)
    )
    status_db.update_analysis_completed_at(analysis_id=analysis_id, completed_at=datetime.now())
