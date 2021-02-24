import logging
from typing import List

import click

from cg.apps.environ import environ_email
from cg.exc import CgError, FlowcellsNeededError
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.cli.workflow.mip.options import (
    OPTION_DRY,
    OPTION_PANEL_BED,
    EMAIL_OPTION,
    PRIORITY_OPTION,
    START_WITH_PROGRAM,
    ARGUMENT_CASE_ID,
)

LOG = logging.getLogger(__name__)


@click.command()
@ARGUMENT_CASE_ID
@click.pass_context
def ensure_flowcells_ondisk(context: click.Context, case_id: str):
    """Check if flowcells are on disk for given case. If not, request flowcells and raise FlowcellsNeededError"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    if not analysis_api.all_flowcells_on_disk(case_id=case_id):
        raise FlowcellsNeededError(
            "Analysis cannot be started: all flowcells need to be on disk to run the analysis"
        )
    LOG.info("All flowcells present on disk")


@click.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """Link FASTQ files for all samples in a case"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    analysis_api.link_fastq_files(case_id=case_id)


@click.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """Link FASTQ files for all samples in a case"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    analysis_api.link_fastq_files(case_id=case_id)


@click.command("config-case")
@OPTION_DRY
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_context
def config_case(context: click.Context, case_id: str, panel_bed: str, dry_run: bool):
    """Generate a config for the case_id"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)

    panel_bed: str = analysis_api.resolve_panel_bed(panel_bed=panel_bed)

    try:
        config_data: dict = analysis_api.pedigree_config(case_id=case_id, panel_bed=panel_bed)
    except CgError as error:
        LOG.error(error.message)
        raise click.Abort()
    if dry_run:
        print(config_data)
        return
    out_path: Path = analysis_api.write_pedigree_config(data=config_data, case_id=case_id)
    LOG.info(f"Config file saved to {out_path}")


@click.command()
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def panel(context: click.Context, case_id: str, dry_run: bool):
    """Write aggregated gene panel file"""

    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    bed_lines: List[str] = analysis_api.panel(case_id=case_id)
    if dry_run:
        for bed_line in bed_lines:
            click.echo(bed_line)
        return
    analysis_api.write_panel(case_id, bed_lines)


@click.command()
@PRIORITY_OPTION
@EMAIL_OPTION
@START_WITH_PROGRAM
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("--mip-dry-run", "mip_dry_run", is_flag=True, help="Run MIP in dry-run mode")
@click.option(
    "--skip-evaluation",
    "skip_evaluation",
    is_flag=True,
    help="Skip mip qccollect evaluation",
)
@click.pass_context
def run(
    context: click.Context,
    case_id: str,
    dry_run: bool = False,
    email: str = None,
    mip_dry_run: bool = False,
    priority: str = None,
    skip_evaluation: bool = False,
    start_with: str = None,
):
    """Run the analysis for a case"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    command_args = dict(
        case=case_id,
        priority=priority or analysis_api.get_priority_for_case(case_id),
        email=email or environ_email(),
        dryrun=mip_dry_run,
        start_with=start_with,
        skip_evaluation=analysis_api.get_skip_evaluation_flag(
            case_id=case_id, skip_evaluation=skip_evaluation
        ),
    )
    analysis_api.check_analysis_ongoing(case_id=case_id)
    analysis_api.run_analysis(case_id=case_id, dry_run=dry_run, command_args=command_args)

    if mip_dry_run:
        LOG.info("Executed MIP in dry-run mode")
        return
    if dry_run:
        LOG.info("Running in dry-run mode. Analysis not submitted to Trailblazer")
        return
    try:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
        LOG.info("MIP rd-dna run started!")
    except CgError as e:
        LOG.error(e.message)
        raise click.Abort


@click.command("resolve-compression")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def resolve_compression(context: click.Context, case_id: str, dry_run: bool):
    """Handles cases where decompression is needed before starting analysis"""
    analysis_api: MipAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.resolve_decompression(case_id=case_id, dry_run=dry_run)
