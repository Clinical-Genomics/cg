import logging
from datetime import datetime
from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import MICROBIAL_APP_TAGS
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.store.models import Analysis, Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def deliver_raw_data_for_analyses(
    analyses: list[Analysis],
    status_db: Store,
    delivery_path: Path,
    service_builder: DeliveryServiceFactory,
    dry_run: bool,
):
    """Deliver raw data for a list of analyses"""
    for analysis in analyses:
        try:
            case: Case = analysis.case
            delivery_service: DeliverFilesService = service_builder.build_delivery_service(
                case=case,
                delivery_type=case.data_delivery,
            )

            delivery_service.deliver_files_for_case(
                case=case, delivery_base_path=delivery_path, dry_run=dry_run
            )
            status_db.update_analysis_upload_started_at(
                analysis_id=analysis.id, upload_started_at=datetime.now()
            )
        except Exception as error:
            status_db.update_analysis_upload_started_at(
                analysis_id=analysis.id, upload_started_at=None
            )
            LOG.error(f"Could not deliver files for analysis {analysis.id}: {error}")
            continue


def get_pseudo_workflow(case: Case) -> str:
    """Return the literal '' if the case is Microbial-fastq, otherwise return the case workflow."""
    tag: str = case.samples[0].application_version.application.tag
    if case.data_analysis == Workflow.RAW_DATA and tag in MICROBIAL_APP_TAGS:
        return "microbial-fastq"
    return case.data_analysis
