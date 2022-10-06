"""Code that handles CLI commands to upload"""
import logging
import sys
import traceback
from typing import Optional

import click

from cg.cli.upload import vogue
from cg.cli.upload.clinical_delivery import auto_fastq, clinical_delivery
from cg.cli.upload.coverage import coverage
from cg.cli.upload.delivery_report import upload_delivery_report_to_scout
from cg.cli.upload.fohm import fohm
from cg.cli.upload.genotype import genotypes
from cg.cli.upload.gisaid import gisaid
from cg.cli.upload.mutacc import process_solved, processed_solved
from cg.cli.upload.nipt import nipt
from cg.cli.upload.observations import observations, available_observations
from cg.cli.upload.scout import (
    create_scout_load_config,
    scout,
    upload_case_to_scout,
    upload_rna_fusion_report_to_scout,
    upload_rna_to_scout,
    upload_rna_junctions_to_scout,
)
from cg.cli.upload.utils import suggest_cases_to_upload
from cg.cli.upload.validate import validate
from cg.constants import Pipeline
from cg.exc import AnalysisAlreadyUploadedError
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.meta.upload.mip_dna.mip_dna import MipDNAUploadAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("-f", "--family", "family_id", help="Upload to all apps")
@click.option(
    "-r",
    "--restart",
    is_flag=True,
    help="Force upload of an analysis that has already been uploaded or marked as started",
)
@click.pass_context
def upload(context: click.Context, family_id: Optional[str], restart: bool):
    """Upload results from analyses"""

    config_object: CGConfig = context.obj
    upload_api = MipDNAUploadAPI(config=config_object)  # default upload API

    LOG.info("----------------- UPLOAD -----------------")

    if context.invoked_subcommand is not None:
        context.obj.meta_apis["upload_api"] = upload_api
    elif family_id:  # Provided case ID without a subcommand: upload everything
        try:
            upload_api.analysis_api.verify_case_id_in_statusdb(case_id=family_id)
            case_obj: models.Family = upload_api.status_db.family(family_id)
            upload_api.verify_analysis_upload(case_obj=case_obj, restart=restart)
        except AnalysisAlreadyUploadedError:
            # Analysis being uploaded or it has been already uploaded
            return

        # Update the upload API based on the data analysis type (MIP-DNA by default)
        if Pipeline.BALSAMIC in case_obj.data_analysis:
            upload_api = BalsamicUploadAPI(config=config_object)

        context.obj.meta_apis["upload_api"] = upload_api
        upload_api.upload(ctx=context, case_obj=case_obj, restart=restart)
        click.echo(click.style(f"{family_id} analysis has been successfully uploaded", fg="green"))
    else:
        suggest_cases_to_upload(status_db=upload_api.status_db)
        raise click.Abort()


@upload.command()
@click.option("--pipeline", type=EnumChoice(Pipeline), help="Limit to specific pipeline")
@click.pass_context
def auto(context: click.Context, pipeline: Pipeline = None):
    """Upload all completed analyses"""

    LOG.info("----------------- AUTO -----------------")

    status_db: Store = context.obj.status_db

    exit_code = 0
    for analysis_obj in status_db.analyses_to_upload(pipeline=pipeline):
        if analysis_obj.family.analyses[0].uploaded_at is not None:
            LOG.warning(
                f"Skipping upload for case {analysis_obj.family.internal_id}. "
                f"It has been already uploaded at {analysis_obj.family.analyses[0].uploaded_at}."
            )
            continue

        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading analysis for case: %s", case_id)
        try:
            context.invoke(upload, family_id=case_id)
        except Exception:
            LOG.error(f"Case {case_id} upload failed")
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


upload.add_command(auto_fastq)
upload.add_command(clinical_delivery)
upload.add_command(coverage)
upload.add_command(create_scout_load_config)
upload.add_command(fohm)
upload.add_command(genotypes)
upload.add_command(gisaid)
upload.add_command(nipt)
upload.add_command(process_solved)
upload.add_command(processed_solved)
upload.add_command(scout)
upload.add_command(upload_case_to_scout)
upload.add_command(upload_delivery_report_to_scout)
upload.add_command(upload_rna_fusion_report_to_scout)
upload.add_command(upload_rna_junctions_to_scout)
upload.add_command(upload_rna_to_scout)
upload.add_command(observations)
upload.add_command(available_observations)
upload.add_command(validate)
upload.add_command(vogue)
