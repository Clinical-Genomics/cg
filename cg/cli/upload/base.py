"""Code that handles upload CLI commands."""
import logging
import sys
import traceback
from typing import Optional

import click
from cg.cli.upload.clinical_delivery import auto_fastq, upload_clinical_delivery
from cg.cli.upload.coverage import upload_coverage
from cg.cli.upload.delivery_report import upload_delivery_report_to_scout
from cg.cli.upload.fohm import fohm
from cg.cli.upload.genotype import upload_genotypes
from cg.cli.upload.gens import upload_to_gens
from cg.cli.upload.gisaid import upload_to_gisaid
from cg.cli.upload.mutacc import process_solved, processed_solved
from cg.cli.upload.nipt import nipt
from cg.cli.upload.observations import (
    upload_available_observations_to_loqusdb,
    upload_observations_to_loqusdb,
)
from cg.cli.upload.scout import (
    create_scout_load_config,
    upload_case_to_scout,
    upload_multiqc_to_scout,
    upload_rna_fusion_report_to_scout,
    upload_rna_junctions_to_scout,
    upload_rna_to_scout,
    upload_to_scout,
)
from cg.cli.upload.utils import suggest_cases_to_upload
from cg.cli.upload.validate import validate
from cg.constants import Pipeline
from cg.exc import AnalysisAlreadyUploadedError
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.meta.upload.mip.mip_dna import MipDNAUploadAPI
from cg.meta.upload.mip.mip_rna import MipRNAUploadAPI
from cg.meta.upload.rnafusion.rnafusion import RnafusionUploadAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("-c", "--case", "case_id", help="Upload to all apps")
@click.option(
    "-r",
    "--restart",
    is_flag=True,
    help="Force upload of an analysis that has already been uploaded or marked as started",
)
@click.pass_context
def upload(context: click.Context, case_id: Optional[str], restart: bool):
    """Upload results from analyses"""

    config_object: CGConfig = context.obj
    upload_api: UploadAPI = MipDNAUploadAPI(config=config_object)  # default upload API

    LOG.info("----------------- UPLOAD -----------------")

    if context.invoked_subcommand is not None:
        context.obj.meta_apis["upload_api"] = upload_api
    elif case_id:  # Provided case ID without a subcommand: upload everything
        try:
            upload_api.analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
            case: Family = upload_api.status_db.get_case_by_internal_id(internal_id=case_id)
            upload_api.verify_analysis_upload(case_obj=case, restart=restart)
        except AnalysisAlreadyUploadedError:
            # Analysis being uploaded or it has been already uploaded
            return

        # Update the upload API based on the data analysis type (MIP-DNA by default)
        # Upload for balsamic, balsamic-umi and balsamic-qc
        if Pipeline.BALSAMIC in case.data_analysis:
            upload_api = BalsamicUploadAPI(config=config_object)
        elif case.data_analysis == Pipeline.RNAFUSION:
            upload_api = RnafusionUploadAPI(config=config_object)
        elif case.data_analysis == Pipeline.MIP_RNA:
            upload_api: UploadAPI = MipRNAUploadAPI(config=config_object)

        context.obj.meta_apis["upload_api"] = upload_api
        upload_api.upload(ctx=context, case=case, restart=restart)
        click.echo(click.style(f"{case_id} analysis has been successfully uploaded", fg="green"))
    else:
        suggest_cases_to_upload(status_db=upload_api.status_db)
        raise click.Abort()


@upload.command("auto")
@click.option("--pipeline", type=EnumChoice(Pipeline), help="Limit to specific pipeline")
@click.pass_context
def upload_all_completed_analyses(context: click.Context, pipeline: Pipeline = None):
    """Upload all completed analyses"""

    LOG.info("----------------- AUTO -----------------")

    status_db: Store = context.obj.status_db

    exit_code = 0
    for analysis_obj in status_db.get_analyses_to_upload(pipeline=pipeline):
        if analysis_obj.family.analyses[0].uploaded_at is not None:
            LOG.warning(
                f"Skipping upload for case {analysis_obj.family.internal_id}. "
                f"It has been already uploaded at {analysis_obj.family.analyses[0].uploaded_at}."
            )
            continue

        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading analysis for case: %s", case_id)
        try:
            context.invoke(upload, case_id=case_id)
        except Exception:
            LOG.error(f"Case {case_id} upload failed")
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


upload.add_command(auto_fastq)
upload.add_command(create_scout_load_config)
upload.add_command(fohm)
upload.add_command(nipt)
upload.add_command(process_solved)
upload.add_command(processed_solved)
upload.add_command(upload_available_observations_to_loqusdb)
upload.add_command(upload_case_to_scout)
upload.add_command(upload_clinical_delivery)
upload.add_command(upload_coverage)
upload.add_command(upload_delivery_report_to_scout)
upload.add_command(upload_genotypes)
upload.add_command(upload_multiqc_to_scout)
upload.add_command(upload_observations_to_loqusdb)
upload.add_command(upload_rna_fusion_report_to_scout)
upload.add_command(upload_rna_junctions_to_scout)
upload.add_command(upload_rna_to_scout)
upload.add_command(upload_to_gens)
upload.add_command(upload_to_gisaid)
upload.add_command(upload_to_scout)
upload.add_command(validate)
