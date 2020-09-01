""" Add CLI support to start MIP rare disease RNA"""

import logging

import click

from cg.apps import hk, lims, scoutapi, tb
from cg.apps.environ import environ_email
from cg.apps.mip.fastq import FastqHandler
from cg.cli.workflow.get_links import get_links
from cg.cli.workflow.mip.store import store as store_cmd
from cg.cli.workflow.mip_rna.deliver import CASE_TAGS, SAMPLE_TAGS
from cg.cli.workflow.mip_rna.deliver import deliver as deliver_cmd
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.mip import AnalysisAPI
from cg.store import Store
from cg.store.utils import case_exists

LOG = logging.getLogger(__name__)


@click.group("mip-rna")
@click.pass_context
def mip_rna(context: click.Context):
    """Rare disease RNA workflow"""

    context.obj["rna_api"] = AnalysisAPI(
        db=context.obj["db"],
        hk_api=hk.HousekeeperAPI(context.obj),
        tb_api=context.obj["tb"],
        scout_api=scoutapi.ScoutAPI(context.obj),
        lims_api=lims.LimsAPI(context.obj),
        deliver_api=DeliverAPI(
            context.obj,
            hk_api=hk.HousekeeperAPI(context.obj),
            lims_api=lims.LimsAPI(context.obj),
            case_tags=CASE_TAGS,
            sample_tags=SAMPLE_TAGS,
        ),
        script=context.obj["mip-rd-rna"]["script"],
        pipeline=context.obj["mip-rd-rna"]["pipeline"],
        conda_env=context.obj["mip-rd-rna"]["conda_env"],
        root=context.obj["mip-rd-rna"]["root"],
    )


@mip_rna.command()
@click.option("-c", "--case", "case_id", help="link all samples for a case")
@click.argument("sample_id", required=False)
@click.pass_context
def link(context: click.Context, case_id: str, sample_id: str):
    """Link FASTQ files for a SAMPLE_ID"""
    rna_api = context.obj["rna_api"]
    link_objs = get_links(rna_api.db, case_id, sample_id)

    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files", link_obj.sample.internal_id, link_obj.sample.data_analysis
        )
        if "mip + rna" in link_obj.sample.data_analysis.lower():
            mip_fastq_handler = FastqHandler(context.obj, rna_api.db, rna_api.tb_api)
            rna_api.link_sample(
                mip_fastq_handler,
                case=link_obj.family.internal_id,
                sample=link_obj.sample.internal_id,
            )


@mip_rna.command()
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.option("-e", "--email", help="email to send errors to")
@click.option("--mip-dry-run", "mip_dry_run", is_flag=True, help="Run MIP in dry-run mode")
@click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
@click.option("-sw", "--start-with", help="start mip from this program.")
@click.argument("case_id")
@click.pass_context
def run(
    context: click.Context,
    case_id: str,
    dry_run: bool = False,
    mip_dry_run: bool = False,
    priority: str = None,
    email: str = None,
    start_with: str = None,
):
    """Run the analysis for a case"""
    rna_api = context.obj["rna_api"]
    case_obj = rna_api.db.family(case_id)

    if not case_exists(case_obj, case_id):
        context.abort()

    if rna_api.tb.analyses(family=case_obj.internal_id, temp=True).first():
        LOG.warning("%s: analysis already running", case_obj.internal_id)
        return

    email = email or environ_email()
    kwargs = dict(
        config=context.obj["mip-rd-rna"]["mip_config"],
        case=case_id,
        priority=priority,
        email=email,
        dryrun=mip_dry_run,
        start_with=start_with,
    )
    if dry_run:
        rna_api.run_command(dry_run=dry_run, **kwargs)
    else:
        rna_api.run_command(**kwargs)
        rna_api.tb.mark_analyses_deleted(case_id=case_id)
        rna_api.tb.add_pending_analysis(case_id=case_id, email=email)
        LOG.info("MIP rd-rna run started!")


@mip_rna.command("config-case")
@click.option("-d", "--dry", is_flag=True, help="Print config to console")
@click.argument("case_id")
@click.pass_context
def config_case(context: click.Context, case_id: str, dry: bool = False):
    """Generate a config for the case_id"""
    rna_api = context.obj["rna_api"]
    case_obj = rna_api.db.family(case_id)

    if not case_exists(case_obj, case_id):
        context.abort()

    # MIP formatted pedigree.yaml config
    config_data = rna_api.config(case_obj, pipeline="mip-rna")

    if dry:
        print(config_data)
    else:
        # Write to trailblazer root dir / case_id
        out_path = rna_api.save_config(config_data)
        LOG.info("saved config to: %s", out_path)


mip_rna.add_command(store_cmd)
mip_rna.add_command(deliver_cmd)
