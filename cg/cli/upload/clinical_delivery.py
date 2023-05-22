"""Code that handles CLI commands to upload"""
import datetime as dt
import logging
from pathlib import Path
from typing import Set

import click
from cg.apps.tb import TrailblazerAPI
from cg.constants import Pipeline
from cg.constants.constants import DRY_RUN
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.constants.priority import PRIORITY_TO_SLURM_QOS
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.store import Store
from cg.store.models import Family
from cgmodels.trailblazer.constants import AnalysisTypes

LOG = logging.getLogger(__name__)


@click.command("clinical-delivery")
@click.pass_context
@click.argument("case_id", required=True)
@DRY_RUN
def upload_clinical_delivery(context: click.Context, case_id: str, dry_run: bool):
    """Links the appropriate files for a case, based on the data_delivery, to the customer folder
    and subsequently uses rsync to upload it to caesar."""

    click.echo(click.style("----------------- Clinical-delivery -----------------"))

    case: Family = context.obj.status_db.get_case_by_internal_id(internal_id=case_id)
    delivery_types: Set[str] = case.get_delivery_arguments()
    is_sample_delivery: bool
    is_case_delivery: bool
    is_complete_delivery: bool
    job_id: int
    is_sample_delivery, is_case_delivery = DeliverAPI.get_delivery_scope(
        delivery_arguments=delivery_types
    )
    if not delivery_types:
        LOG.info(f"No delivery of files requested for case {case_id}")
        return

    LOG.debug("Delivery types are: %s", delivery_types)
    for delivery_type in delivery_types:
        DeliverAPI(
            store=context.obj.status_db,
            hk_api=context.obj.housekeeper_api,
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
            delivery_type=delivery_type,
            project_base_path=Path(context.obj.delivery_path),
        ).deliver_files(case_obj=case)

    rsync_api: RsyncAPI = RsyncAPI(context.obj)
    is_complete_delivery, job_id = rsync_api.slurm_rsync_single_case(
        case=case,
        dry_run=dry_run,
        sample_files_present=is_sample_delivery,
        case_files_present=is_case_delivery,
    )
    RsyncAPI.write_trailblazer_config(
        {"jobs": [str(job_id)]}, config_path=rsync_api.trailblazer_config_path
    )
    analysis_name: str = f"{case_id}_rsync" if is_complete_delivery else f"{case_id}_partial"
    if not dry_run:
        context.obj.trailblazer_api.add_pending_analysis(
            case_id=analysis_name,
            analysis_type=AnalysisTypes.OTHER,
            config_path=rsync_api.trailblazer_config_path.as_posix(),
            out_dir=rsync_api.log_dir.as_posix(),
            slurm_quality_of_service=PRIORITY_TO_SLURM_QOS[case.priority],
            data_analysis=Pipeline.RSYNC,
            ticket=case.latest_ticket,
        )
    LOG.info("Transfer of case %s started with SLURM job id %s", case_id, job_id)


@click.command("all-fastq")
@click.pass_context
@DRY_RUN
def auto_fastq(context: click.Context, dry_run: bool):
    """Starts upload of all not previously uploaded cases with analysis type fastq to
    clinical-delivery."""

    status_db: Store = context.obj.status_db
    trailblazer_api: TrailblazerAPI = context.obj.trailblazer_api
    for analysis_obj in status_db.get_analyses_to_upload(pipeline=Pipeline.FASTQ):
        if analysis_obj.family.analyses[0].uploaded_at:
            LOG.warning(
                "Newer analysis already uploaded for %s, skipping",
                analysis_obj.family.internal_id,
            )
            continue
        if analysis_obj.upload_started_at:
            if trailblazer_api.is_latest_analysis_completed(
                case_id=analysis_obj.family.internal_id
            ):
                LOG.info(
                    "The upload for %s is completed, setting uploaded at to %s",
                    analysis_obj.family.internal_id,
                    dt.datetime.now(),
                )
                analysis_obj.uploaded_at = dt.datetime.now()
            else:
                LOG.warning(
                    "Upload to clinical-delivery for %s has already started, skipping",
                    analysis_obj.family.internal_id,
                )
            continue
        case: Family = analysis_obj.family
        LOG.info("Uploading family: %s", case.internal_id)
        analysis_obj.upload_started_at = dt.datetime.now()
        context.invoke(upload_clinical_delivery, case_id=case.internal_id, dry_run=dry_run)
        if not dry_run:
            status_db.session.commit()
