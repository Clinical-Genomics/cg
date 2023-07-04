"""CLI support to start microsalt"""

import datetime as dt
import logging
from pathlib import Path
from typing import Any, List, Optional

import click
from cg.cli.workflow.commands import resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.constants.constants import FileFormat
from cg.exc import CgError
from cg.io.controller import WriteStream, WriteFile
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Sample
from housekeeper.store.models import File
from cg.meta.workflow.analysis import AnalysisAPI

LOG = logging.getLogger(__name__)

OPTION_DRY_RUN = click.option(
    "-d",
    "--dry-run",
    help="Print command to console without executing",
    is_flag=True,
)
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


@click.group(invoke_without_command=True)
@click.pass_context
def microsalt(context: click.Context) -> None:
    """Microbial workflow"""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = MicrosaltAnalysisAPI(
        config=context.obj,
    )


microsalt.add_command(store)
microsalt.add_command(store_available)
microsalt.add_command(resolve_compression)


@microsalt.command()
@OPTION_TICKET
@OPTION_SAMPLE
@OPTION_DRY_RUN
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
@OPTION_DRY_RUN
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
    sample_objs: List[Sample] = analysis_api.get_samples(case_id=case_id, sample_id=sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        raise click.Abort

    parameters: List[dict] = [analysis_api.get_parameters(sample_obj) for sample_obj in sample_objs]
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
    LOG.info("Saved config %s", config_case_path)


@microsalt.command()
@OPTION_DRY_RUN
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
            "Trailblazer warning: Could not track analysis progress for case %s! %s",
            case_id,
            error.__class__.__name__,
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
@OPTION_DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@click.pass_context
def start(
    context: click.Context, ticket: bool, sample: bool, unique_id: str, dry_run: bool
) -> None:
    """Start whole microSALT workflow by providing case, ticket or sample id"""
    LOG.info("Starting Microsalt workflow for %s", unique_id)

    context.invoke(link, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)
    context.invoke(config_case, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)
    context.invoke(run, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)


@microsalt.command("start-available")
@OPTION_DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, unique_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred: {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@microsalt.command("qc-microsalt")
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def qc_microsalt(context: click.Context, unique_id: str) -> None:
    """Perform QC on a microsalt case."""
    analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]
    try:
        analysis_api.microsalt_qc(
            case_id=unique_id,
            run_dir_path=analysis_api.get_latest_case_path(case_id=unique_id),
            lims_project=analysis_api.get_project(
                analysis_api.status_db.get_case_by_internal_id(internal_id=unique_id)
                .samples[0]
                .internal_id
            ),
        )
    except IndexError:
        LOG.error(f"No existing analysis directories found for case {unique_id}.")
