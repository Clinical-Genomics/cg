""" Add CLI support to start MIP rare disease RNA"""

import logging

import click

from cg.apps.environ import environ_email
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.get_links import get_links
from cg.cli.workflow.mip.store import store as store_cmd
from cg.constants import Pipeline
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store
from cg.store.utils import case_exists

LOG = logging.getLogger(__name__)


@click.group("mip-rna")
@click.pass_context
def mip_rna(context: click.Context):
    """Rare disease RNA workflow"""
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)
    context.obj["lims_api"] = LimsAPI(context.obj)
    context.obj["status_db"] = Store(context.obj["database"])

    context.obj["rna_api"] = MipAnalysisAPI(
        db=context.obj["status_db"],
        hk_api=context.obj["housekeeper_api"],
        tb_api=context.obj["trailblazer_api"],
        scout_api=context.obj["scout_api"],
        lims_api=context.obj["lims_api"],
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
    """Link FASTQ files for a sample_id"""
    rna_api = context.obj["rna_api"]
    link_objs = get_links(rna_api.db, case_id, sample_id)

    for link_obj in link_objs:
        LOG.info(
            "%s: %s link FASTQ files", link_obj.sample.internal_id, link_obj.family.data_analysis
        )
        if not link_obj.family.data_analysis:
            LOG.warning(
                f"No analysis set for {link_obj.sample.internal_id}, file will still be linked"
            )
            rna_api.link_sample(sample=link_obj.sample, case_id=link_obj.family.internal_id)
        if link_obj.family.data_analysis == str(Pipeline.MIP_RNA):
            rna_api.link_sample(sample=link_obj.sample, case_id=link_obj.family.internal_id)


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
        raise click.Abort()
    if rna_api.get_analyses_from_trailblazer(case_id=case_obj.internal_id, temp=True):
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
        return

    rna_api.run_command(**kwargs)

    if mip_dry_run:
        LOG.info("Executed MIP in dry-run mode - skipping Trailblazer step")
        return

    rna_api.mark_analyses_deleted(case_id=case_id)
    rna_api.add_pending_analysis(
        case_id=case_id,
        email=email,
        type=rna_api.get_application_type(case_id),
        out_dir=rna_api.get_case_output_path(case_id).as_posix(),
        config_path=rna_api.get_slurm_job_ids_path(case_id).as_posix(),
        priority="normal",
        data_analysis=Pipeline.MIP_RNA,
    )
    rna_api.set_statusdb_action(case_id=case_id, action="running")
    LOG.info("MIP rd-rna run started!")


@mip_rna.command("config-case")
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="Print pedigree config to console")
@click.argument("case_id")
@click.pass_context
def config_case(context: click.Context, case_id: str, dry_run: bool = False):
    """Generate a pedigree config for the case"""
    rna_api = context.obj["rna_api"]

    case_obj = rna_api.db.family(case_id)
    if not case_exists(case_obj, case_id):
        LOG.error("Case %s does not exist!", case_id)
        context.abort()
    config_data = rna_api.pedigree_config(case_obj, pipeline=Pipeline.MIP_RNA)
    if dry_run:
        click.echo(config_data)
        return
    out_path = rna_api.write_pedigree_config(
        data=config_data,
        out_dir=rna_api.get_case_output_path(case_id),
        pedigree_config_path=rna_api.get_pedigree_config_path(case_id),
    )
    LOG.info(f"Config saved to: {out_path}")


mip_rna.add_command(store_cmd)
