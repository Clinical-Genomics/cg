import logging
from pathlib import Path

from cg.apps.tb.api import TrailblazerAPI
from cg.constants.tb import AnalysisStatus
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import read_yaml
from cg.store.models import Analysis
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def perform_qc(
    analysis_id: int, root_directory: Path, status_db: Store, trailblazer_api: TrailblazerAPI
) -> None:
    # TODO parse case deliverables file
    # TODO consider: checking for file integrity of some files
    # TODO inform prodbio info via slack (if high prio) of failure and mark as failed in Trailblazer
    # TODO validate that there is content in the case deliverables file
    # TODO set analysis completed_at in StatusDB to now if success <--- (New behavior?)
    # TODO publish event if success
    analysis: Analysis = status_db.get_analysis_by_entry_id_strict(analysis_id)
    case_id = analysis.case_internal_id
    case_deliverables_file = Path(root_directory, case_id, f"{case_id}_deliverables.yaml")
    case_deliverables: list[dict] = read_yaml(case_deliverables_file)

    missing_files = []
    for deliverable in case_deliverables:
        for file in deliverable["paths"]:
            if deliverable["mandatory"] and not Path(file).is_file():
                missing_files.append(file)

    if missing_files:
        raise MandatoryFileMissingError(f"Missing files: {missing_files}")

    trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.COMPLETED)
