"""Commands to start MIP rare disease DNA workflow"""

import logging
import sys

import click

from cg.apps import hk, lims, scoutapi, tb
from cg.apps.environ import environ_email
from cg.cli.workflow.get_links import get_links
from cg.cli.workflow.mip.store import store as store_cmd
from cg.cli.workflow.mip_dna.deliver import CASE_TAGS, SAMPLE_TAGS
from cg.cli.workflow.mip_dna.deliver import deliver as deliver_cmd
from cg.constants import EXIT_SUCCESS
from cg.exc import CgError
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.mip import AnalysisAPI
from cg.store import Store
from cg.store.utils import case_exists

LOG = logging.getLogger(__name__)
EMAIL_OPTION = click.option("-e", "--email", help="email to send errors to", type=str)
PRIORITY_OPTION = click.option(
    "-p", "--priority", default="normal", type=click.Choice(["low", "normal", "high"])
)
START_WITH_PROGRAM = click.option(
    "-sw", "--start-with", help="start mip from this program.", type=str
)


@click.group("mip-dna", invoke_without_command=True)
@EMAIL_OPTION
@PRIORITY_OPTION
@START_WITH_PROGRAM
@click.option("-c", "--case", "case_id", help="case to prepare and start an analysis for", type=str)
@click.pass_context
def mip_dna(context: click.Context, case_id: str, email: str, priority: str, start_with: str):
    """Rare disease DNA workflow"""
    context.obj["dna_api"] = AnalysisAPI(
        db=Store(context.obj["database"]),
        hk_api=hk.HousekeeperAPI(context.obj),
        tb_api=tb.TrailblazerAPI(context.obj),
        scout_api=scoutapi.ScoutAPI(context.obj),
        lims_api=lims.LimsAPI(context.obj),
        deliver_api=DeliverAPI(
            context.obj,
            hk_api=hk.HousekeeperAPI(context.obj),
            lims_api=lims.LimsAPI(context.obj),
            case_tags=CASE_TAGS,
            sample_tags=SAMPLE_TAGS,
        ),
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
    context.invoke(config_case, case_id=case_id)
    context.invoke(link, case_id=case_id)
    context.invoke(panel, case_id=case_id)
    context.invoke(run, case_id=case_id, priority=priority, email=email, start_with=start_with)


@mip_dna.command()
@click.option("-c", "--case", "case_id", help="link all samples for a case", type=str)
@click.argument("sample_id", required=False)
@click.pass_context
def link(context: click.Context, case_id: str, sample_id: str):
    """Link FASTQ files for a sample_id"""
    dna_api = context.obj["dna_api"]
    link_objs = get_links(dna_api.db, case_id, sample_id)
    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files", link_obj.sample.internal_id, link_obj.sample.data_analysis
        )
        # This block is necessary to handle cases where data analysis is not set in ClinicalDB for old samples
        if not link_obj.sample.data_analysis:
            LOG.warning(
                f"No analysis set for {link_obj.sample.internal_id}, file will still be linked"
            )
            dna_api.link_sample(sample=link_obj.sample, case_id=case_id)
            return

        if "mip" in link_obj.sample.data_analysis.lower():
            dna_api.link_sample(sample=link_obj.sample, case_id=case_id)
            return


@mip_dna.command("config-case")
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.argument("case_id", required=False, type=str)
@click.pass_context
def config_case(context: click.Context, case_id: str, dry_run: bool = False):
    """Generate a config for the case_id"""
    dna_api = context.obj["dna_api"]
    if case_id is None:
        _suggest_cases_to_analyze(context)
        return

    case_obj = dna_api.db.family(case_id)
    if not case_exists(case_obj, case_id):
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort()

    try:
        config_data = dna_api.pedigree_config(case_obj, pipeline="mip-dna")
    except CgError as error:
        LOG.error(error.message)
        raise click.Abort()
    if dry_run:
        print(config_data)
        return
    out_path = dna_api.write_pedigree_config(config_data)
    LOG.info(f"Config file saved to {out_path}")


@mip_dna.command()
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print output to console")
@click.argument("case_id", required=False, type=str)
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
@click.argument("case_id", required=False, type=str)
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.option("--mip-dry-run", "mip_dry_run", is_flag=True, help="Run MIP in dry-run mode")
@click.option(
    "--skip-evaluation", "skip_evaluation", is_flag=True, help="Skip mip qccollect evaluation"
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
        raise click.Abort()

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

    if dna_api.tb.is_analysis_ongoing(case_id=case_obj.internal_id):
        LOG.warning("%s: analysis is ongoing - skipping", case_obj.internal_id)
        return

    if dna_api.get_skip_evaluation_flag(case_obj=case_obj):
        kwargs["skip_evaluation"] = True

    if dry_run:
        dna_api.run_command(dry_run=dry_run, **kwargs)
        return

    dna_api.run_command(**kwargs)
    dna_api.tb.mark_analyses_deleted(case_id=case_id)
    dna_api.tb.add_pending_analysis(case_id=case_id, email=email)
    dna_api.set_statusdb_action(case_id=case_id, action="running")
    LOG.info("MIP rd-dna run started!")


@mip_dna.command()
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.pass_context
def start(context: click.Context, dry_run: bool = False):
    """Start all cases that are ready for analysis"""
    dna_api = context.obj["dna_api"]

    cases = [case_obj for case_obj in dna_api.db.cases_to_analyze(pipeline="mip")]
    for case_obj in cases:
        if not dna_api.is_dna_only_case(case_obj):
            LOG.warning("%s: contains non-dna samples - skipping", case_obj.internal_id)
            continue
        LOG.info("%s: start analysis", case_obj.internal_id)
        has_started = dna_api.tb.has_analysis_started(case_id=case_obj.internal_id)
        if has_started:
            status = dna_api.tb.get_analysis_status(case_id=case_obj.internal_id)
            LOG.warning("%s: analysis is %s - skipping", case_obj.internal_id, status)
            continue
        if dry_run:
            continue
        try:
            context.invoke(
                mip_dna,
                priority=dna_api.get_priority(case_obj),
                case_id=case_obj.internal_id,
            )
        except (CgError, click.Abort) as error:
            LOG.error(error.message)
            continue


def _suggest_cases_to_analyze(context: click.Context, show_as_error: bool = False):
    """Suggest cases to analyze"""
    if show_as_error:
        LOG.error("provide a case, suggestions:")
    else:
        LOG.warning("provide a case, suggestions:")
    for case_obj in context.obj["dna_api"].db.cases_to_analyze(pipeline="mip", limit=50):
        click.echo(case_obj)


mip_dna.add_command(store_cmd)
mip_dna.add_command(deliver_cmd)
