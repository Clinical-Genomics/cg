"""Code that handles upload CLI commands."""

import logging
import sys
import traceback

import rich_click as click

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
    upload_rna_alignment_file_to_scout,
    upload_rna_fusion_report_to_scout,
    upload_rna_junctions_to_scout,
    upload_rna_omics_to_scout,
    upload_rna_to_scout,
    upload_to_scout,
    upload_tomte_to_scout,
)
from cg.cli.upload.utils import suggest_cases_to_upload
from cg.cli.upload.validate import validate
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants import Workflow
from cg.exc import AnalysisAlreadyUploadedError
from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.meta.upload.microsalt.microsalt_upload_api import MicrosaltUploadAPI
from cg.meta.upload.mip.mip_dna import MipDNAUploadAPI
from cg.meta.upload.mip.mip_rna import MipRNAUploadAPI
from cg.meta.upload.mutant.mutant import MutantUploadAPI
from cg.meta.upload.nallo.nallo import NalloUploadAPI
from cg.meta.upload.nf_analysis import NfAnalysisUploadAPI
from cg.meta.upload.raredisease.raredisease import RarediseaseUploadAPI
from cg.meta.upload.tomte.tomte import TomteUploadAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case
from cg.store.store import Store
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("-c", "--case", "case_id", help="Upload to all apps")
@click.option(
    "-r",
    "--restart",
    is_flag=True,
    help="Force upload of an analysis that has already been uploaded or marked as started",
)
@click.pass_context
def upload(context: click.Context, case_id: str | None, restart: bool):
    """Upload results from analyses"""

    config_object: CGConfig = context.obj
    upload_api: UploadAPI = MipDNAUploadAPI(config_object)

    LOG.info("----------------- UPLOAD -----------------")

    if context.invoked_subcommand is not None:
        context.obj.meta_apis["upload_api"] = upload_api
    elif case_id:  # Provided case ID without a subcommand: upload everything
        try:
            upload_api.analysis_api.status_db.verify_case_exists(case_id)
            case: Case = upload_api.status_db.get_case_by_internal_id(case_id)
            upload_api.verify_analysis_upload(case_obj=case, restart=restart)
        except AnalysisAlreadyUploadedError:
            # Analysis being uploaded or it has been already uploaded
            return

        if Workflow.BALSAMIC in case.data_analysis:
            upload_api = BalsamicUploadAPI(config_object)
        elif case.data_analysis == Workflow.MIP_RNA:
            upload_api = MipRNAUploadAPI(config_object)
        elif case.data_analysis == Workflow.MICROSALT:
            upload_api = MicrosaltUploadAPI(config_object)
        elif case.data_analysis == Workflow.NALLO:
            upload_api = NalloUploadAPI(config_object)
        elif case.data_analysis == Workflow.RAREDISEASE:
            upload_api = RarediseaseUploadAPI(config_object)
        elif case.data_analysis == Workflow.TOMTE:
            upload_api = TomteUploadAPI(config_object)
        elif case.data_analysis in {
            Workflow.RNAFUSION,
            Workflow.TAXPROFILER,
        }:
            upload_api = NfAnalysisUploadAPI(config_object, case.data_analysis)
        elif case.data_analysis == Workflow.MUTANT:
            upload_api = MutantUploadAPI(config_object)

        context.obj.meta_apis["upload_api"] = upload_api
        upload_api.upload(ctx=context, case=case, restart=restart)
        click.echo(click.style(f"{case_id} analysis has been successfully uploaded", fg="green"))
    else:
        suggest_cases_to_upload(status_db=upload_api.status_db)
        raise click.Abort()


@upload.command("auto")
@click.option("--workflow", type=EnumChoice(Workflow), help="Limit to specific workflow")
@click.pass_context
def upload_all_completed_analyses(context: click.Context, workflow: Workflow = None):
    """Upload all completed analyses."""

    LOG.info("----------------- AUTO -----------------")

    status_db: Store = context.obj.status_db

    exit_code = 0
    for analysis in status_db.get_analyses_to_upload(workflow=workflow):
        latest_case_analysis: Analysis = status_db.get_latest_completed_analysis_for_case(
            analysis.case.internal_id
        )
        if latest_case_analysis.uploaded_at is not None:
            LOG.warning(
                f"Skipping upload for case {analysis.case.internal_id}. "
                f"Case has been already uploaded at {latest_case_analysis.uploaded_at}."
            )
            continue

        case_id = analysis.case.internal_id
        LOG.info(f"Uploading analysis for case: {case_id}")
        try:
            context.invoke(upload, case_id=case_id)
        except Exception:
            LOG.error(f"Case {case_id} upload failed")
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


upload.add_command(create_scout_load_config)
upload.add_command(fohm)
upload.add_command(nipt)
upload.add_command(process_solved)
upload.add_command(processed_solved)
upload.add_command(upload_available_observations_to_loqusdb)
upload.add_command(upload_case_to_scout)
upload.add_command(upload_coverage)
upload.add_command(upload_delivery_report_to_scout)
upload.add_command(upload_genotypes)
upload.add_command(upload_multiqc_to_scout)
upload.add_command(upload_observations_to_loqusdb)
upload.add_command(upload_rna_alignment_file_to_scout)
upload.add_command(upload_rna_fusion_report_to_scout)
upload.add_command(upload_rna_junctions_to_scout)
upload.add_command(upload_rna_omics_to_scout)

upload.add_command(upload_rna_to_scout)
upload.add_command(upload_tomte_to_scout)
upload.add_command(upload_to_gens)
upload.add_command(upload_to_gisaid)
upload.add_command(upload_to_scout)
upload.add_command(validate)
