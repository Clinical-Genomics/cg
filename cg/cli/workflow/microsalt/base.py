"""CLI support to start microsalt"""

import logging
from pathlib import Path
from typing import Any

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN
from cg.constants.constants import FileFormat
from cg.exc import AnalysisNotReadyError, CgError
from cg.io.controller import WriteFile, WriteStream
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Sample

LOG = logging.getLogger(__name__)

OPTION_SAMPLE = click.option(
    "-s",
    "--sample",
    help="Start workflow by providing a sample_id (By default case_id will be used)",
    is_flag=True,
)
OPTION_TICKET = click.option(
    "-t",
    "--ticket",
    help="Start workflow by providing a ticket_id (By default case_id will be used)",
    is_flag=True,
)
ARGUMENT_UNIQUE_IDENTIFIER = click.argument("unique_id", required=True, type=click.STRING)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def microsalt(context: click.Context) -> None:
    """Microbial workflow"""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = MicrosaltAnalysisAPI(config=context.obj)


microsalt.add_command(store)
microsalt.add_command(store_available)
microsalt.add_command(resolve_compression)


@microsalt.command()
@OPTION_TICKET
@OPTION_SAMPLE
@DRY_RUN
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_obj
def link(context: CGConfig, ticket: bool, sample: bool, unique_id: str, dry_run: bool) -> None:
    """Link microbial FASTQ files to dedicated analysis folder for a given case, ticket or sample"""
    if dry_run:
        return
    analysis_api: MicrosaltAnalysisAPI = context.meta_apis["analysis_api"]
    case_id, sample_id = analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )
    analysis_api.link_fastq_files(
        case_id=case_id,
        sample_id=sample_id,
    )


@microsalt.command("config-case")
@DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_obj
def config_case(
    context: CGConfig, dry_run: bool, ticket: bool, sample: bool, unique_id: str
) -> None:
    """Create a config file for a case or a sample analysis in microSALT"""

    analysis_api: MicrosaltAnalysisAPI = context.meta_apis["analysis_api"]
    case_id, sample_id = analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )
    sample_objs: list[Sample] = analysis_api.get_samples(case_id=case_id, sample_id=sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        raise click.Abort

    parameters: list[dict] = [analysis_api.get_parameters(sample_obj) for sample_obj in sample_objs]
    filename: str = sample_id or case_id
    config_case_path: Path = analysis_api.get_config_path(filename=filename)
    if dry_run:
        click.echo(
            WriteStream.write_stream_from_content(content=parameters, file_format=FileFormat.JSON)
        )
        return
    WriteFile.write_file_from_content(
        content=parameters, file_format=FileFormat.JSON, file_path=config_case_path
    )
    LOG.info(f"Saved config {config_case_path}")


@microsalt.command()
@DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@ARGUMENT_UNIQUE_IDENTIFIER
@click.option(
    "-c",
    "--config-case",
    "config_case_path",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="optionally change the config-case",
)
@click.pass_obj
def run(
    context: CGConfig,
    dry_run: bool,
    config_case_path: click.Path,
    ticket: bool,
    sample: bool,
    unique_id: Any,
) -> None:
    """Start microSALT workflow by providing case, ticket or sample id"""

    analysis_api: MicrosaltAnalysisAPI = context.meta_apis["analysis_api"]
    case_id, sample_id = analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )
    fastq_path: Path = analysis_api.get_case_fastq_path(case_id=case_id)
    if not config_case_path:
        filename = sample_id or case_id
        config_case_path: Path = analysis_api.get_config_path(filename=filename)

    if not sample_id:
        analyse_command = [
            "analyse",
            config_case_path.absolute().as_posix(),
            "--input",
            fastq_path.absolute().as_posix(),
        ]
    else:
        analyse_command = [
            "analyse",
            config_case_path.absolute().as_posix(),
            "--input",
            Path(fastq_path, sample_id).absolute().as_posix(),
        ]

    if sample_id or dry_run:
        analysis_api.process.run_command(parameters=analyse_command, dry_run=dry_run)
        return
    try:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
    except Exception as error:
        LOG.warning(
            f"Trailblazer warning: Could not track analysis progress for case {case_id}! {error.__class__.__name__}"
        )
    try:
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
        analysis_api.process.run_command(parameters=analyse_command, dry_run=dry_run)
    except:
        LOG.error("Failed to run analysis!")
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
        raise


@microsalt.command()
@ARGUMENT_UNIQUE_IDENTIFIER
@DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@click.pass_context
def start(
    context: click.Context, ticket: bool, sample: bool, unique_id: str, dry_run: bool
) -> None:
    """Start whole microSALT workflow by providing case, ticket or sample id"""
    LOG.info(f"Starting Microsalt workflow for {unique_id}")
    if not (sample or ticket):
        analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]
        analysis_api.prepare_fastq_files(case_id=unique_id, dry_run=dry_run)
    context.invoke(link, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)
    context.invoke(config_case, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)
    context.invoke(run, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)


@microsalt.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_ready_for_analysis():
        try:
            context.invoke(start, unique_id=case.internal_id, dry_run=dry_run)
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


@microsalt.command("qc")
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def qc_microsalt(context: click.Context, unique_id: str) -> None:
    """Perform QC on a microsalt case."""
    analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]
    metrics_file_path: Path = analysis_api.get_metrics_file_path(unique_id)
    try:
        LOG.info(f"Performing QC on case {unique_id}")
        analysis_api.quality_checker.quality_control(metrics_file_path)
    except IndexError:
        LOG.error(f"No existing analysis directories found for case {unique_id}.")
