"""Commands to start MIP rare disease DNA workflow"""

import logging
from pathlib import Path
from typing import List

import click

from cg.apps.crunchy import CrunchyAPI
from cg.apps.environ import environ_email
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip.store import store as store_cmd
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.exc import CgError, DecompressionNeededError, FlowcellsNeededError
from cg.meta.compress import CompressAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store, models

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
    "-d",
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Print to console instead of executing",
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    type=str,
    help="Set this option to override fetching of panel name from LIMS",
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)


@click.group("mip-dna", invoke_without_command=True)
@click.pass_context
def mip_dna(
    context: click.Context,
):
    """Rare disease DNA workflow"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)
    context.obj["lims_api"] = LimsAPI(context.obj)
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["crunchy_api"] = CrunchyAPI(context.obj)
    context.obj["compress_api"] = CompressAPI(
        hk_api=context.obj["housekeeper_api"], crunchy_api=context.obj["crunchy_api"]
    )
    context.obj["prepare_fastq_api"] = PrepareFastqAPI(
        context.obj["status_db"], context.obj["compress_api"]
    )

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


@mip_dna.command()
@ARGUMENT_CASE_ID
@click.pass_context
def ensure_flowcells_ondisk(context: click.Context, case_id: str):
    """Check if flowcells are on disk for given case. If not, request flowcells and raise FlowcellsNeededError"""
    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    case_obj: models.Family = dna_api.db.family(case_id)
    if not case_obj:
        LOG.error("Case %s does not exist in Status-DB", case_id)
        raise click.Abort

    all_flowcells_ondisk: bool = dna_api.check_flowcells_ondisk(case_obj)
    if not all_flowcells_ondisk:
        LOG.warning(
            f"Case {case_obj.internal_id} not ready to run!",
        )
        # Commit the updates to request flowcells
        dna_api.db.commit()
        raise FlowcellsNeededError(
            "Analysis cannot be started: all flowcells need to be on disk to run the analysis"
        )
    LOG.info("All flowcells present on disk")


@mip_dna.command()
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """Link FASTQ files for all samples in a case"""
    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    case_obj: models.Family = dna_api.db.family(case_id)
    link_objs: List[models.FamilySample] = case_obj.links
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
def config_case(context: click.Context, case_id: str, panel_bed: str, dry_run: bool):
    """Generate a config for the case_id"""
    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    case_obj: models.Family = dna_api.db.family(case_id)
    if not case_obj:
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort()

    panel_bed: str = dna_api.resolve_panel_bed(panel_bed=panel_bed)

    try:
        config_data: dict = dna_api.pedigree_config(
            case_obj, panel_bed=panel_bed, pipeline=Pipeline.MIP_DNA
        )
    except CgError as error:
        LOG.error(error.message)
        raise click.Abort()
    if dry_run:
        print(config_data)
        return
    out_path: Path = dna_api.write_pedigree_config(
        data=config_data,
        out_dir=dna_api.get_case_output_path(case_id),
        pedigree_config_path=dna_api.get_pedigree_config_path(case_id),
    )
    LOG.info(f"Config file saved to {out_path}")


@mip_dna.command()
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def panel(context: click.Context, case_id: str, dry_run: bool):
    """Write aggregated gene panel file"""

    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    case_obj: models.Family = dna_api.db.family(case_id)
    bed_lines: List[str] = dna_api.panel(case_obj)
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
    dna_api: MipAnalysisAPI = context.obj["dna_api"]

    case_obj: models.Family = dna_api.db.family(case_id)
    if not case_obj:
        LOG.error(f"Case {case_id} does not exist!")
        raise click.Abort

    email: str = email or environ_email()
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


@mip_dna.command("resolve-compression")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def resolve_compression(context: click.Context, case_id: str, dry_run: bool):
    """Handles cases where decompression is needed before starting analysis"""
    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    prepare_fastq_api: PrepareFastqAPI = context.obj["prepare_fastq_api"]
    status_db: Store = dna_api.db
    case_obj: models.Family = status_db.family(case_id)
    if not case_obj:
        LOG.error("Case %s does not exist in status-db", case_id)
        raise click.Abort
    decompression_needed = prepare_fastq_api.is_spring_decompression_needed(case_obj.internal_id)

    if decompression_needed:
        LOG.info(
            "The analysis for %s could not start, decompression is needed",
            case_obj.internal_id,
        )
        decompression_possible = prepare_fastq_api.can_at_least_one_sample_be_decompressed(
            case_obj.internal_id
        )
        if decompression_possible:
            possible_to_start_decompression = (
                prepare_fastq_api.can_at_least_one_decompression_job_start(
                    case_obj.internal_id, dry_run
                )
            )
            if possible_to_start_decompression:
                if not dry_run:
                    dna_api.set_statusdb_action(case_id=case_id, action="analyze")
                LOG.info(
                    "Decompression started for %s",
                    case_obj.internal_id,
                )
            else:
                LOG.warning(
                    "Decompression failed to start for %s",
                    case_obj.internal_id,
                )
        else:
            LOG.warning(
                "Decompression can not be started for %s",
                case_obj.internal_id,
            )
        raise DecompressionNeededError("Workflow interrupted: decompression is not finished")

    if prepare_fastq_api.is_spring_decompression_running(case_obj.internal_id):
        raise DecompressionNeededError("Workflow interrupted: decompression is running")

    LOG.info("Linking fastq files in housekeeper for case %s", case_id)
    prepare_fastq_api.check_fastq_links(case_obj.internal_id)

    if prepare_fastq_api.is_spring_decompression_needed(case_obj.internal_id):
        raise DecompressionNeededError("Workflow interrupted: decompression is not finished")

    LOG.info("Decompression for case %s not needed, starting analysis", case_id)


@mip_dna.command()
@PRIORITY_OPTION
@EMAIL_OPTION
@START_WITH_PROGRAM
@OPTION_PANEL_BED
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
def start(
    context: click.Context,
    case_id: str,
    dry_run: bool,
    email: str,
    mip_dry_run: bool,
    priority: str,
    skip_evaluation: bool,
    start_with: str,
    panel_bed: str,
):
    """Start full MIP-DNA analysis workflow for a case"""

    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    status_db: Store = dna_api.db
    case_obj: models.Family = status_db.family(case_id)
    if not case_obj:
        LOG.error("Case %s does not exist in Status-DB", case_id)
        raise click.Abort
    LOG.info("Starting full MIP-DNA analysis workflow for case %s", case_id)

    analysis_ongoing = dna_api.is_latest_analysis_ongoing(case_id=case_obj.internal_id)
    if analysis_ongoing:
        status = dna_api.get_latest_analysis_status(case_id=case_obj.internal_id)
        LOG.warning(f"{case_obj.internal_id}: analysis status is {status} - skipping")
        return
    try:
        context.invoke(ensure_flowcells_ondisk, case_id=case_id)
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id)
        context.invoke(panel, case_id=case_id, dry_run=dry_run)
        context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
        context.invoke(
            run,
            case_id=case_id,
            priority=priority,
            email=email,
            start_with=start_with,
            dry_run=dry_run,
            mip_dry_run=mip_dry_run,
            skip_evaluation=skip_evaluation,
        )
    except (FlowcellsNeededError, DecompressionNeededError) as e:
        LOG.error(e.message)


@mip_dna.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full MIP-DNA analysis workflow for all cases ready for analysis"""
    dna_api: MipAnalysisAPI = context.obj["dna_api"]
    exit_code: int = EXIT_SUCCESS
    for case_obj in dna_api.db.cases_to_analyze(pipeline=Pipeline.MIP_DNA, threshold=0.75):
        if not dna_api.is_dna_only_case(case_obj):
            LOG.warning("%s: contains non-dna samples - skipping", case_obj.internal_id)
            continue
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


mip_dna.add_command(store_cmd)
