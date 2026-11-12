import logging
from pathlib import Path

from cg.apps.tb.api import TrailblazerAPI
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def perform_qc(
    case_id: str, root_directory: Path, status_db: Store, trailblazer_api: TrailblazerAPI
) -> None:
    # TODO parse case deliverables file
    # TODO validate all mandatory files are in place (in the case directory)
    # TODO consider: checking for file integrity of some files
    # TODO inform prodbio info via slack of failure and mark as failed in Trailblazer
    pass

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
