"""CLI support to create config and/or start BALSAMIC """

import logging
import traceback

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.base import report_deliver, store, store_available, store_housekeeper
from cg.cli.workflow.balsamic.options import OPTION_PANEL_BED, OPTION_WORKFLOW_PROFILE
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, link, resolve_compression
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Sex
from cg.constants.cli_options import DRY_RUN, LIMIT
from cg.constants.constants import GenomeVersion
from cg.constants.priority import SlurmQos
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case

LOG = logging.getLogger(__name__)

OPTION_GENDER = click.option(
    "--gender",
    type=click.Choice([Sex.FEMALE, Sex.MALE]),
    required=False,
    help="Case associated gender. Set this option to override the one selected by the customer in StatusDB.",
)
OPTION_GENOME_VERSION = click.option(
    "--genome-version",
    show_default=True,
    default=GenomeVersion.HG19,
    type=click.Choice([GenomeVersion.HG19, GenomeVersion.HG38, GenomeVersion.CANFAM3]),
    help="Type and build version of the reference genome. Set this option to override the default.",
)
OPTION_QOS = click.option(
    "-qos",
    "--slurm-quality-of-service",
    type=click.Choice([SlurmQos.LOW, SlurmQos.NORMAL, SlurmQos.HIGH, SlurmQos.EXPRESS]),
    help="Job priority in SLURM. Setting this option will override the StatusDB case priority.",
)
OPTION_PON_CNN = click.option(
    "--pon-cnn",
    type=click.Path(exists=True),
    required=False,
    help="Panel of normal reference (.cnn) for CNVkit",
)
OPTION_OBSERVATIONS = click.option(
    "--observations",
    type=click.Path(exists=True),
    multiple=True,
    required=False,
    help="VCF paths of clinical and/or cancer SNVs and SVs observations (WHOLE_GENOME_SEQUENCING analysis only). Set this option to "
    "override the latest Loqusdb dump files.",
)
OPTION_CACHE_VERSION = click.option(
    "--cache-version",
    type=click.STRING,
    required=False,
    help="Cache version to be used for init or analysis. Use 'develop' or 'X.X.X'.",
)


@click.group(
    "balsamic-umi",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.pass_context
def balsamic_umi(context: click.Context):
    """Cancer analysis workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicUmiAnalysisAPI(config=config)


@balsamic_umi.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_OBSERVATIONS
@OPTION_CACHE_VERSION
@DRY_RUN
@click.pass_obj
def config_case(
    context: CGConfig,
    case_id: str,
    gender: str,
    genome_version: str,
    panel_bed: str,
    pon_cnn: click.Path,
    observations: list[click.Path],
    cache_version: str,
    dry_run: bool,
):
    """Create config file for BALSAMIC UMI analysis for a given CASE_ID."""

    analysis_api: BalsamicUmiAnalysisAPI = context.meta_apis["analysis_api"]
    try:
        LOG.info(f"Creating config file for {case_id}.")
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(
            case_id=case_id,
            gender=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            observations=observations,
            cache_version=cache_version,
            dry_run=dry_run,
        )
    except CgError as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not create config: {error_info}")
        raise click.Abort()
    except Exception as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not create config: {error_info}")
        raise click.Abort()


@balsamic_umi.command("run")
@ARGUMENT_CASE_ID
@OPTION_WORKFLOW_PROFILE
@DRY_RUN
@OPTION_QOS
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    workflow_profile: click.Path,
    slurm_quality_of_service: str,
    dry_run: bool,
):
    """Run Balsamic UMI analysis for given CASE ID"""
    analysis_api: BalsamicUmiAnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.check_analysis_ongoing(case_id)
        analysis_api.run_analysis(
            case_id=case_id,
            workflow_profile=workflow_profile,
            slurm_quality_of_service=slurm_quality_of_service,
            dry_run=dry_run,
        )
        if dry_run:
            return
        analysis_api.on_analysis_started(case_id)
    except Exception as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not run analysis: {error_info}")
        raise click.Abort()


@balsamic_umi.command("start")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_QOS
@DRY_RUN
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_CACHE_VERSION
@OPTION_OBSERVATIONS
@OPTION_WORKFLOW_PROFILE
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    gender: str,
    genome_version: str,
    cache_version: str,
    panel_bed: str,
    pon_cnn: str,
    observations: list[click.Path],
    slurm_quality_of_service: str,
    workflow_profile: click.Path,
    dry_run: bool,
):
    """Start full workflow for case ID."""
    analysis_api: BalsamicUmiAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    LOG.info(f"Starting analysis for {case_id}")
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(
        config_case,
        case_id=case_id,
        gender=gender,
        genome_version=genome_version,
        cache_version=cache_version,
        panel_bed=panel_bed,
        pon_cnn=pon_cnn,
        observations=observations,
        dry_run=dry_run,
    )
    context.invoke(
        run,
        case_id=case_id,
        workflow_profile=workflow_profile,
        slurm_quality_of_service=slurm_quality_of_service,
        dry_run=dry_run,
    )


@balsamic_umi.command("start-available")
@DRY_RUN
@LIMIT
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False, limit: int | None = None):
    """Start full workflow for all cases ready for analysis"""

    analysis_api: BalsamicUmiAnalysisAPI = context.obj.meta_apis["analysis_api"]

    cases: list[Case] = analysis_api.get_cases_to_analyze(limit=limit)
    LOG.info(f"Starting {len(cases)} available Balsamic UMI cases")

    exit_code: int = EXIT_SUCCESS
    for case in cases:
        try:
            context.invoke(start, case_id=case.internal_id, dry_run=dry_run)
        except AnalysisNotReadyError as error:
            LOG.error(error)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred: {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


balsamic_umi.add_command(resolve_compression)
balsamic_umi.add_command(link)
balsamic_umi.add_command(report_deliver)
balsamic_umi.add_command(store_housekeeper)
balsamic_umi.add_command(store)
balsamic_umi.add_command(store_available)
