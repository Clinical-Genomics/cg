"""Commands to start MIP rare disease dna workflow"""

import logging
import sys

import click

from cg.apps import hk, lims, scoutapi, tb
from cg.apps.mip.fastq import FastqHandler
from cg.cli.workflow.get_links import get_links
from cg.cli.workflow.mip.store import store as store_cmd
from cg.cli.workflow.mip_dna.deliver import CASE_TAGS, SAMPLE_TAGS
from cg.cli.workflow.mip_dna.deliver import deliver as deliver_cmd
from cg.exc import CgError
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.mip_dna import AnalysisAPI
from cg.store import Store

LOG = logging.getLogger(__name__)
EMAIL_OPTION = click.option("-e", "--email", help="email to send errors to")
PRIORITY_OPTION = click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
START_WITH_PROGRAM = click.option("-sw", "--start-with", help="start mip from this program.")


@click.group("mip-dna", invoke_without_command=True)
@EMAIL_OPTION
@PRIORITY_OPTION
@START_WITH_PROGRAM
@click.option("-c", "--case", "case_id", help="case to prepare and start an analysis for")
@click.pass_context
def mip_dna(context: click.Context, case_id: str, email: str, priority: str, start_with: str):
    """Rare disease DNA workflow"""
    context.obj["db"] = Store(context.obj["database"])
    hk_api = hk.HousekeeperAPI(context.obj)
    scout_api = scoutapi.ScoutAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)
    context.obj["tb"] = tb.TrailblazerAPI(context.obj)
    deliver = DeliverAPI(
        context.obj, hk_api=hk_api, lims_api=lims_api, case_tags=CASE_TAGS, sample_tags=SAMPLE_TAGS
    )
    context.obj["api"] = AnalysisAPI(
        db=context.obj["db"],
        hk_api=hk_api,
        tb_api=context.obj["tb"],
        scout_api=scout_api,
        lims_api=lims_api,
        deliver_api=deliver,
    )
    context.obj["dna_api"] = MipAPI(
        context.obj["trailblazer"]["script"], context.obj["trailblazer"]["pipeline"]
    )

    if context.invoked_subcommand is None:
        if case_id is None:
            _suggest_cases_to_analyze(context, show_as_error=True)
            context.abort()

        # check everything is ok
        case_obj = context.obj["db"].family(case_id)
        if case_obj is None:
            LOG.error("%s: not found", case_id)
            context.abort()
        is_ok = context.obj["api"].check(case_obj)
        if not is_ok:
            LOG.warning("%s: not ready to run", case_obj.internal_id)
            # commit the updates to request flowcells
            context.obj["db"].commit()
        else:
            # execute the analysis!
            context.invoke(config_case, case_id=case_id)
            context.invoke(link, case_id=case_id)
            context.invoke(panel, case_id=case_id)
            context.invoke(
                run, case_id=case_id, priority=priority, email=email, start_with=start_with
            )


@mip_dna.command()
@click.option("-c", "--case", "case_id", help="link all samples for a case")
@click.argument("sample_id", required=False)
@click.pass_context
def link(context: click.Context, case_id: str, sample_id: str):
    """Link FASTQ files for a SAMPLE_ID"""
    store = context.obj["db"]

    link_objs = get_links(store, case_id, sample_id)

    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files", link_obj.sample.internal_id, link_obj.sample.data_analysis
        )
        if not link_obj.sample.data_analysis or "mip" in link_obj.sample.data_analysis.lower():
            mip_fastq_handler = FastqHandler(context.obj, context.obj["db"], context.obj["tb"])
            context.obj["api"].link_sample(
                mip_fastq_handler,
                case=link_obj.family.internal_id,
                sample=link_obj.sample.internal_id,
            )


@mip_dna.command("config-case")
@click.option("-d", "--dry", is_flag=True, help="Print config to console")
@click.argument("case_id", required=False)
@click.pass_context
def config_case(context: click.Context, case_id: str, dry: bool = False):
    """Generate a config for the CASE_ID"""
    if case_id is None:
        _suggest_cases_to_analyze(context)
        context.abort()

    case_obj = context.obj["db"].family(case_id)

    if not case_obj:
        LOG.error("Case %s not found", case_id)
        context.abort()

    # pipeline formatted pedigree.yaml config
    config_data = context.obj["api"].config(case_obj)

    if dry:
        print(config_data)
    else:
        # Write to trailblazer root dir / case_id
        out_path = context.obj["tb"].save_config(config_data)
        LOG.info("saved config to %s", out_path)


mip_dna.add_command(config_case)


@mip_dna.command()
@click.option("-p", "--print", "print_output", is_flag=True, help="print to console")
@click.argument("case_id", required=False)
@click.pass_context
def panel(context: click.Context, case_id: str, print_output: bool = False):
    """Write aggregated gene panel file"""
    if case_id is None:
        _suggest_cases_to_analyze(context)
        context.abort()

    case_obj = context.obj["db"].family(case_id)
    bed_lines = context.obj["api"].panel(case_obj)
    if print_output:
        for bed_line in bed_lines:
            print(bed_line)
    else:
        context.obj["tb"].write_panel(case_id, bed_lines)


@mip_dna.command()
@PRIORITY_OPTION
@EMAIL_OPTION
@START_WITH_PROGRAM
@click.argument("case_id", required=False)
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.pass_context
def run(
    context: click.Context,
    case_id: str,
    dry: bool = False,
    email: str = None,
    priority: str = None,
    start_with: str = None,
):
    """Run the analysis for a case"""
    kwargs = dict(
        config=context.obj["trailblazer"]["mip_config"],
        case=case_id,
        priority=priority,
        email=email,
        dryrun=dry,
        start_with=start_with,
    )
    if case_id is None:
        _suggest_cases_to_analyze(context)
        context.abort()

    case_obj = context.obj["db"].family(case_id)
    if case_obj is None:
        LOG.error("%s: case not found", case_id)
        context.abort()
    if context.obj["tb"].analyses(family=case_obj.internal_id, temp=True).first():
        LOG.warning("%s: analysis already running", {case_obj.internal_id})
    if dry:
        command = dna_api.build_command(**kwargs)
        LOG.info(" ".join(command))
    else:
        context.obj["api"].run(case_obj, priority=priority, email=email, start_with=start_with)


@mip_dna.command()
@click.option(
    "-d", "--dry-run", "dry_run", is_flag=True, help="print to console, " "without actualising"
)
@click.pass_context
def start(context: click.Context, dry_run: bool = False):
    """Start all cases that are ready for analysis"""
    exit_code = 0

    cases = [case_obj.internal_id for case_obj in context.obj["db"].cases_to_mip_analyze()]

    for case_id in cases:

        case_obj = context.obj["db"].family(case_id)

        if AnalysisAPI.is_dna_only_case(case_obj):
            LOG.info("%s: start analysis", case_obj.internal_id)
        else:
            LOG.warning("%s: contains non-dna samples, skipping", case_obj.internal_id)
            continue

        priority = (
            "high" if case_obj.high_priority else ("low" if case_obj.low_priority else "normal")
        )

        if dry_run:
            continue

        try:
            context.invoke(mip_dna, priority=priority, case_id=case_obj.internal_id)
        except tb.MipStartError as error:
            LOG.error(error.message)
            exit_code = 1
        except CgError as error:
            LOG.error(error.message)
            exit_code = 11
    sys.exit(exit_code)


def _suggest_cases_to_analyze(context, show_as_error: bool = False):
    """Suggest cases to analyze"""
    if show_as_error:
        LOG.error("provide a case, suggestions:")
    else:
        LOG.warning("provide a case, suggestions:")
    for case_obj in context.obj["db"].cases_to_mip_analyze()[:50]:
        click.echo(case_obj)


mip_dna.add_command(store_cmd)
mip_dna.add_command(deliver_cmd)
