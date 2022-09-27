"""Code that handles CLI commands to upload"""
import datetime as dt
import logging

from pathlib import Path

import click

from cg.constants import Pipeline, DataDelivery
from cg.constants.constants import DRY_RUN
from cg.meta.workflow.analysis import AnalysisAPI
from cg.store import Store, models

from cg.apps.tb import TrailblazerAPI
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.constants.priority import PRIORITY_TO_SLURM_QOS
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def fastq(context: click.Context):
    context.obj.meta_apis["delivery_api"] = DeliverAPI(
        store=context.obj.status_db,
        hk_api=context.obj.housekeeper_api,
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[DataDelivery.FASTQ]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[DataDelivery.FASTQ]["sample_tags"],
        delivery_type=DataDelivery.FASTQ,
        project_base_path=Path(context.obj.delivery_path),
    )
    context.obj.meta_apis["rsync_api"] = RsyncAPI(context.obj)


@fastq.command("all-available")
@click.pass_context
@DRY_RUN
def auto_fastq(context: click.Context, dry_run: bool):
    """Starts upload of all not previously uploaded cases with analysis type fastq to
    clinical-delivery"""

    status_db: Store = context.obj.status_db
    trailblazer_api: TrailblazerAPI = context.obj.trailblazer_api
    for analysis_obj in status_db.analyses_to_upload(pipeline=Pipeline.FASTQ):
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
                if not dry_run:
                    status_db.commit()
            else:
                LOG.warning(
                    "Upload to clinical-delivery for %s has already started, skipping",
                    analysis_obj.family.internal_id,
                )
            continue
        case: models.Family = analysis_obj.family
        analysis_obj.upload_started_at = dt.datetime.now()
        LOG.info("Uploading family: %s", case.internal_id)
        context.invoke(upload_fastq, case_id=case.internal_id, dry_run=dry_run)
        status_db.commit()


@fastq.command("case")
@click.pass_context
@click.argument("case_id", required=True)
@DRY_RUN
def upload_fastq(context: click.Context, case_id: str, dry_run: bool):
    """Uploads fastq files for a case to clinical-delivery"""

    status_db: Store = context.obj.status_db
    deliver_api: DeliverAPI = context.obj.meta_apis["delivery_api"]
    rsync_api: RsyncAPI = context.obj.meta_apis["rsync_api"]
    trailblazer_api: TrailblazerAPI = context.obj.trailblazer_api

    case: models.Family = status_db.family(internal_id=case_id)
    deliver_api.deliver_files(case)
    job_id: int = rsync_api.slurm_rsync_single_case(
        case_id=case_id, dry_run=dry_run, sample_files_present=True
    )
    rsync_api.write_trailblazer_config(
        {"jobs": [str(job_id)]}, config_path=rsync_api.trailblazer_config_path
    )
    if not dry_run:
        trailblazer_api.add_pending_analysis(
            case_id=case_id,
            analysis_type=AnalysisAPI.get_application_type(
                status_db.family(case_id).links[0].sample
            ),
            config_path=str(rsync_api.trailblazer_config_path),
            out_dir=str(rsync_api.log_dir),
            slurm_quality_of_service=PRIORITY_TO_SLURM_QOS[case.priority],
            data_analysis=Pipeline.FASTQ,
        )
    LOG.info("Transfer of case %s started with SLURM job id %s", case_id, job_id)
