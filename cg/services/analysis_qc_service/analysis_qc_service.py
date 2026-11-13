import logging
from pathlib import Path

from cg.apps.tb.api import TrailblazerAPI
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import read_yaml
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def perform_qc(
    case_id: str, root_directory: Path, status_db: Store, trailblazer_api: TrailblazerAPI
) -> None:
    # TODO parse case deliverables file
    # TODO validate all mandatory files are in place (in the case directory)
    # TODO consider: checking for file integrity of some files
    # TODO inform prodbio info via slack (if high prio) of failure and mark as failed in Trailblazer
    # TODO set TB to completed if success
    # TODO set analysis completed_at in StatusDB to now if success
    # TODO publish event if success
    case_deliverables_file = Path(root_directory, case_id, f"{case_id}_deliverables.yaml")
    case_deliverables: list[dict] = read_yaml(case_deliverables_file)

    missing_files = []
    for deliverable in case_deliverables:
        for file in deliverable["paths"]:
            if deliverable["mandatory"] and not Path(file).is_file():
                missing_files.append(file)

    if missing_files:
        raise MandatoryFileMissingError(f"Missing files: {missing_files}")

    # multi_qc_parser = MultiQCParser(status_db)
    # file = Path(root_directory, case_id, MultiQC.MULTIQC, MultiQC.MULTIQC_DATA, "multiqc_data.json")
    # try:
    #     multi_qc_parser.parse_and_validate(case_id=case_id, file=file)
    # except MetricsQCError as error:
    #     LOG.error(f"QC metrics failed for {case_id}, with: {error}")
    #     trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.FAILED)
    #     samples = status_db.get_samples_by_case_id(case_id=case_id)
    #     for sample in samples:
    #         # TODO improve!
    #         trailblazer_comment = str(error).replace(
    #             f"{sample.internal_id} - ", f"{sample.name} ({sample.internal_id}) - "
    #         )
    #     trailblazer_api.add_comment(case_id=case_id, comment=trailblazer_comment)
    #     raise MetricsQCError from error
