"""Commands to start MIP rare disease DNA workflow"""

import logging

import click

from cg.apps.environ import environ_email
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip.store import store as store_cmd
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.exc import CgError
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store
from cg.store.utils import case_exists

LOG = logging.getLogger(__name__)
EMAIL_OPTION = click.option("-e", "--email", help="Email to send errors to", type=str)
PRIORITY_OPTION = click.option(
    "-p",
    "--priority",
    default="normal",
    type=click.Choice(["low", "normal", "high"]),
)
START_WITH_PROGRAM = click.option(
    "-sw", "--start-with", help="Start mip from this program.", type=str
)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry_run", is_flag=True, help="Print to console instead of executing"
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    type=str,
    help="Set this option to override fetching of panel name from LIMS",
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)


@click.group("mip-dna", invoke_without_command=True)
@EMAIL_OPTION
@PRIORITY_OPTION
@OPTION_PANEL_BED
@START_WITH_PROGRAM
@OPTION_DRY
@click.option(
    "-c",
    "--case",
    "case_id",
    help="case to prepare and start an analysis for",
    type=str,
)
@click.pass_context
def mip_dna(
    context: click.Context,
    case_id: str,
    email: str,
    priority: str,
    panel_bed: str,
    start_with: str,
    dry_run: bool,
):
    """Rare disease DNA workflow"""
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)
    context.obj["lims_api"] = LimsAPI(context.obj)
    context.obj["status_db"] = Store(context.obj["database"])

    context.obj["dna_api"] = MipAnalysisAPI(
        db=context.obj["status_db"],
        hk_api=context.obj["housekeeper_api"],
        tb_api=context.obj["trailblazer_api"],
        scout_api=context.obj["scout_api"],
        lims_api=context.obj["lims_api"],
        script=context.obj["mip-rd-dna"]["script"],
        pipeline=context.obj["mip-rd-dna"]["pipeline"],
        conda_env=context.obj["mip-rd-dna"]["conda_env"],
        root=context.obj["mip-rd-dna"]["root"],
    )
    dna_api = context.obj["dna_api"]

    if context.invoked_subcommand is not None:
        return

    if case_id is None:
        click.echo(context.get_help())
        return

    case_obj = dna_api.db.family(case_id)
    if not case_exists(case_obj, case_id):
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort()

    all_flowcells_ondisk = dna_api.check(case_obj)
    if not all_flowcells_ondisk:
        LOG.warning(
            f"Case {case_obj.internal_id} not ready to run!",
        )
        # Commit the updates to request flowcells
        dna_api.db.commit()
        return

    # Invoke full workflow
    context.invoke(link, case_id=case_id)
    context.invoke(panel, case_id=case_id, dry_run=dry_run)
    context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
    context.invoke(
        run, case_id=case_id, priority=priority, email=email, start_with=start_with, dry_run=dry_run
    )


@mip_dna.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """Link FASTQ files for a sample_id"""
    dna_api = context.obj["dna_api"]
    case_obj = dna_api.db.family(case_id)
    link_objs = case_obj.links
    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files",
            link_obj.sample.internal_id,
            link_obj.family.data_analysis,
        )
        # This block is necessary to handle cases where data analysis is not set in ClinicalDB for old samples
        if not link_obj.family.data_analysis:
            LOG.warning(
                f"No analysis set for {link_obj.sample.internal_id}, file will still be linked"
            )
            dna_api.link_sample(sample=link_obj.sample, case_id=link_obj.family.internal_id)

        if link_obj.family.data_analysis == str(Pipeline.MIP_DNA):
            dna_api.link_sample(sample=link_obj.sample, case_id=link_obj.family.internal_id)


@mip_dna.command("config-case")
@OPTION_DRY
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_context
def config_case(context: click.Context, case_id: str, panel_bed: str, dry_run: bool = False):
    """Generate a config for the case_id"""
    dna_api = context.obj["dna_api"]
    if case_id is None:
        _suggest_cases_to_analyze(context)
        return

    case_obj = dna_api.db.family(case_id)
    if not case_exists(case_obj, case_id):
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort()

    panel_bed = dna_api.resolve_panel_bed(panel_bed=panel_bed)

    try:
        config_data = dna_api.pedigree_config(
            case_obj, panel_bed=panel_bed, pipeline=Pipeline.MIP_DNA
        )
    except CgError as error:
        LOG.error(error.message)
        raise click.Abort()
    if dry_run:
        print(config_data)
        return
    out_path = dna_api.write_pedigree_config(
        data=config_data,
        out_dir=dna_api.get_case_output_path(case_id),
        pedigree_config_path=dna_api.get_pedigree_config_path(case_id),
    )
    LOG.info(f"Config file saved to {out_path}")


@mip_dna.command()
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def panel(context: click.Context, case_id: str, dry_run: bool = False):
    """Write aggregated gene panel file"""

    dna_api = context.obj["dna_api"]
    case_obj = dna_api.db.family(case_id)
    bed_lines = dna_api.panel(case_obj)
    if dry_run:
        for bed_line in bed_lines:
            click.echo(bed_line)
        return
    dna_api.write_panel(case_id, bed_lines)


@mip_dna.command()
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
    dna_api = context.obj["dna_api"]

    if case_id is None:
        _suggest_cases_to_analyze(context)
        return
    case_obj = dna_api.db.family(case_id)
    if not case_exists(case_obj, case_id):
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort

    email = email or environ_email()
    kwargs = dict(
        config=context.obj["mip-rd-dna"]["mip_config"],
        case=case_id,
        priority=priority or dna_api.get_priority(case_obj),
        email=email,
        dryrun=mip_dry_run,
        start_with=start_with,
        skip_evaluation=skip_evaluation,
    )

    if dna_api.is_latest_analysis_ongoing(case_id=case_obj.internal_id):
        LOG.warning(f"{case_obj.internal_id} : analysis is still ongoing - skipping")
        return

    if dna_api.get_skip_evaluation_flag(case_obj=case_obj):
        kwargs["skip_evaluation"] = True

    dna_api.run_command(dry_run=dry_run, **kwargs)

    if mip_dry_run:
        LOG.info("Executed MIP in dry-run mode")
        return

    if dry_run:
        LOG.info("Running in dry-run mode. Analysis not submitted to Trailblazer")
        return

    try:
        dna_api.mark_analyses_deleted(case_id=case_id)
        dna_api.add_pending_analysis(
            case_id=case_id,
            email=email,
            type=dna_api.get_application_type(case_id),
            out_dir=dna_api.get_case_output_path(case_id).as_posix(),
            config_path=dna_api.get_slurm_job_ids_path(case_id).as_posix(),
            priority=dna_api.get_priority(case_obj),
            data_analysis=Pipeline.MIP_DNA,
        )
        dna_api.set_statusdb_action(case_id=case_id, action="running")
        LOG.info("MIP rd-dna run started!")
    except CgError as e:
        LOG.error(e.message)
        raise click.Abort


@mip_dna.command()
@OPTION_DRY
@click.pass_context
def start(context: click.Context, dry_run: bool = False):
    """Start all cases that are ready for analysis"""
    dna_api = context.obj["dna_api"]
    exit_code = EXIT_SUCCESS
    for case_obj in dna_api.db.cases_to_analyze(pipeline=Pipeline.MIP_DNA, threshold=0.75):
        if not dna_api.is_dna_only_case(case_obj):
            LOG.warning("%s: contains non-dna samples - skipping", case_obj.internal_id)
            continue
        LOG.info(
            f"{case_obj.internal_id}: start analysis",
        )
        has_started = dna_api.has_latest_analysis_started(case_id=case_obj.internal_id)
        if has_started:
            status = dna_api.get_latest_analysis_status(case_id=case_obj.internal_id)
            LOG.warning(f"{case_obj.internal_id}: analysis is {status} - skipping")
            continue
        if dry_run:
            continue
        try:
            context.invoke(
                mip_dna,
                priority=dna_api.get_priority(case_obj),
                case_id=case_obj.internal_id,
            )
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred - {e.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


def _suggest_cases_to_analyze(context: click.Context, show_as_error: bool = False):
    """Suggest cases to analyze"""
    if show_as_error:
        LOG.error("provide a case, suggestions:")
    else:
        LOG.warning("provide a case, suggestions:")
    for case_obj in context.obj["dna_api"].db.cases_to_analyze(pipeline=Pipeline.MIP_DNA, limit=50):
        LOG.info(case_obj)


mip_dna.add_command(store_cmd)
