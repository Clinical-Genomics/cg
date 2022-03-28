import logging

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_DRY, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.send_fastq import SendFastqAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def send_fastq(context: click.Context):
    """Deliver fastq files to caesar"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj.meta_apis["analysis_api"] = SendFastqAnalysisAPI(config=context.obj)


@send_fastq.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Send fastq files for fastq-cases which have not yet been delivered"""

    analysis_api: SendFastqAnalysisAPI = context.obj.meta_apis["analysis_api"]
    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        case_id = case_obj.internal_id
        try:
            context.invoke(start, case_id=case_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error("Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@send_fastq.command("start")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def start(context: click.Context, dry_run: bool, case_id: str) -> None:
    """Send fastq files for given fastq-case"""
    LOG.info("Starting delivery of fastq files for %s to caesar", case_id)
    try:
        context.invoke(run, case_id=case_id, dry_run=dry_run)
    except DecompressionNeededError:
        LOG.info("Workflow not ready to run, can continue after decompression")


@send_fastq.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    dry_run: bool = False,
):
    """Deliver fastq files for a case"""

    analysis_api: SendFastqAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)

    analysis_api.check_analysis_ongoing(case_id=case_id)
    case: models.Family = analysis_api.status_db.family(internal_id=case_id)

    if dry_run:
        LOG.info("Running %s in dry-run mode.", case_id)
        return

    try:
        job_id: int = analysis_api.run_transfer(case=case, case_id=case_id, dry_run=dry_run)
        LOG.info("Transfer of case %s started with SLURM job id %s", case_id, job_id)
    except CgError as e:
        LOG.error(e.message)
        raise click.Abort


send_fastq.add_command(store)
send_fastq.add_command(store_available)
