import logging
from typing import List

import click

from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.exc import FlowcellsNeededError
from cg.meta.workflow.analysis import AnalysisAPI

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry_run", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.command("ensure-flowcells-ondisk")
@ARGUMENT_CASE_ID
@click.pass_context
def ensure_flowcells_ondisk(context: click.Context, case_id: str):
    """Check if flowcells are on disk for given case. If not, request flowcells and raise FlowcellsNeededError"""
    analysis_api: AnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    if not analysis_api.all_flowcells_on_disk(case_id=case_id):
        raise FlowcellsNeededError(
            "Analysis cannot be started: all flowcells need to be on disk to run the analysis"
        )
    LOG.info("All flowcells present on disk")


@click.command("resolve-compression")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def resolve_compression(context: click.Context, case_id: str, dry_run: bool):
    """Handles cases where decompression is needed before starting analysis"""
    analysis_api: AnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.resolve_decompression(case_id=case_id, dry_run=dry_run)


@click.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """Link FASTQ files for all samples in a case"""
    analysis_api: AnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    analysis_api.link_fastq_files(case_id=case_id)


@click.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool):
    """
    Store finished analysis files in Housekeeper
    """
    analysis_api: AnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    if dry_run:
        LOG.info("Dry run: Would have stored deliverables for %s", case_id)
        return
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
    except Exception as exception_object:
        analysis_api.housekeeper_api.rollback()
        analysis_api.status_db.rollback()
        LOG.error("Error storing deliverables for case %s - %s", case_id, exception_object)
        raise


@click.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """
    Store bundles for all finished analyses in Housekeeper
    """
    analysis_api: AnalysisAPI = context.obj["analysis_api"]
    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error("Error storing %s: %s", case_obj.internal_id, exception_object)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
