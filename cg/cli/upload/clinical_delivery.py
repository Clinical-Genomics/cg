"""Code that handles CLI commands to upload"""

import datetime as dt
import logging
from pathlib import Path

import click

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Priority, Workflow
from cg.constants.cli_options import DRY_RUN
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.constants.tb import AnalysisTypes
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("clinical-delivery")
@click.pass_context
@click.argument("case_id", required=True)
@DRY_RUN
def upload_clinical_delivery(context: click.Context, case_id: str, dry_run: bool):
    """Links the appropriate files for a case, based on the data_delivery, to the customer folder
    and subsequently uses rsync to upload it to caesar."""

    click.echo(click.style("----------------- Clinical-delivery -----------------"))

    case: Case = context.obj.status_db.get_case_by_internal_id(internal_id=case_id)
    delivery_types: set[str] = case.get_delivery_arguments()
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

    LOG.debug(f"Delivery types are: {delivery_types}")
    for delivery_type in delivery_types:
        DeliverAPI(
            store=context.obj.status_db,
            hk_api=context.obj.housekeeper_api,
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
            delivery_type=delivery_type,
            project_base_path=Path(context.obj.delivery_path),
            fastq_file_service=FastqConcatenationService(),
        ).deliver_files(case_obj=case)

    rsync_api: RsyncAPI = RsyncAPI(context.obj)
    is_complete_delivery, job_id = rsync_api.slurm_rsync_single_case(
        case=case,
        dry_run=dry_run,
        sample_files_present=is_sample_delivery,
        case_files_present=is_case_delivery,
    )
    RsyncAPI.write_trailblazer_config(
        content={"jobs": [str(job_id)]},
        config_path=rsync_api.trailblazer_config_path,
        dry_run=dry_run,
    )
    analysis_name: str = f"{case_id}_rsync" if is_complete_delivery else f"{case_id}_partial"
    order_id: int = case.latest_order.id
    if not dry_run:
        trailblazer_api: TrailblazerAPI = context.obj.trailblazer_api
        analysis: TrailblazerAnalysis = trailblazer_api.add_pending_analysis(
            case_id=analysis_name,
            analysis_type=AnalysisTypes.OTHER,
            config_path=rsync_api.trailblazer_config_path.as_posix(),
            order_id=order_id,
            out_dir=rsync_api.log_dir.as_posix(),
            slurm_quality_of_service=Priority.priority_to_slurm_qos().get(case.priority),
            workflow=Workflow.RSYNC,
            ticket=case.latest_ticket,
        )
        trailblazer_api.add_upload_job_to_analysis(analysis_id=analysis.id, slurm_id=job_id)

        analysis_service: AnalysisService = context.obj.analysis_service
        analysis_service.add_upload_job(slurm_id=job_id, case_id=case_id)

    LOG.info(f"Transfer of case {case_id} started with SLURM job id {job_id}")


@click.command("all-fastq")
@click.pass_context
@DRY_RUN
def auto_fastq(context: click.Context, dry_run: bool):
    """Starts upload of all not previously uploaded cases with analysis type fastq to
    clinical-delivery."""
    exit_code: int = EXIT_SUCCESS
    status_db: Store = context.obj.status_db
    trailblazer_api: TrailblazerAPI = context.obj.trailblazer_api
    for analysis_obj in status_db.get_analyses_to_upload(workflow=Workflow.FASTQ):
        if analysis_obj.case.analyses[0].uploaded_at:
            LOG.debug(
                f"Newer analysis already uploaded for {analysis_obj.case.internal_id}, skipping"
            )
            continue
        if analysis_obj.upload_started_at:
            if trailblazer_api.is_latest_analysis_completed(case_id=analysis_obj.case.internal_id):
                LOG.info(
                    f"The upload for {analysis_obj.case.internal_id} is completed, setting uploaded at to {dt.datetime.now()}"
                )
                analysis_obj.uploaded_at = dt.datetime.now()
            else:
                LOG.debug(
                    f"Upload to clinical-delivery for {analysis_obj.case.internal_id} has already started, skipping"
                )
            continue
        case: Case = analysis_obj.case
        LOG.info(f"Uploading family: {case.internal_id}")
        analysis_obj.upload_started_at = dt.datetime.now()
        try:
            context.invoke(upload_clinical_delivery, case_id=case.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Upload of case {case.internal_id} failed")
            LOG.error(error)
            exit_code: int = EXIT_FAIL
            continue

    if not dry_run:
        status_db.session.commit()

    if exit_code == EXIT_FAIL:
        raise click.Abort
