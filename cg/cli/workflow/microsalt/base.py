"""CLI support to start microsalt"""

import json
import logging
from pathlib import Path
from typing import Any

import click

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.store import Store

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
def microsalt(context: click.Context):
    """Microbial workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    microsalt_analysis_api = MicrosaltAnalysisAPI(
        db=Store(context.obj["database"]),
        hk_api=HousekeeperAPI(context.obj),
        lims_api=LimsAPI(context.obj),
        trailblazer_api=TrailblazerAPI(context.obj),
        hermes_api=HermesApi(context.obj),
        config=context.obj["microsalt"],
    )
    context.obj["microsalt_analysis_api"] = microsalt_analysis_api


@microsalt.command()
@OPTION_TICKET
@OPTION_SAMPLE
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def link(context: click.Context, ticket: bool, sample: bool, unique_id: str):
    """Link microbial FASTQ files to dedicated analysis folder for a given case, ticket or sample"""

    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]

    case_id, sample_id = microsalt_analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )

    if not microsalt_analysis_api.check_flowcells_on_disk(case_id=case_id, sample_id=sample_id):
        raise click.Abort
    microsalt_analysis_api.link_samples(
        case_id=case_id,
        sample_id=sample_id,
    )


@microsalt.command("config-case")
@OPTION_DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def config_case(context: click.Context, dry_run: bool, ticket: bool, sample: bool, unique_id: str):
    """ Create a config file for a case or a sample analysis in microSALT """

    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]

    case_id, sample_id = microsalt_analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )

    sample_objs = microsalt_analysis_api.get_samples(case_id=case_id, sample_id=sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        raise click.Abort

    parameters = [microsalt_analysis_api.get_parameters(sample_obj) for sample_obj in sample_objs]

    filename = sample_id or case_id
    config_case_path: Path = microsalt_analysis_api.get_config_path(filename=filename)
    if dry_run:
        click.echo(json.dumps(parameters, indent=4, sort_keys=True))
        return

    with open(config_case_path, "w") as outfile:
        json.dump(parameters, outfile, indent=4, sort_keys=True)
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
@click.pass_context
def run(
    context: click.Context,
    dry_run: bool,
    config_case_path: click.Path,
    ticket: bool,
    sample: bool,
    unique_id: Any,
):
    """ Start microSALT workflow by providing case, ticket or sample id """

    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]

    case_id, sample_id = microsalt_analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )

    fastq_path: Path = microsalt_analysis_api.get_case_fastq_path(case_id=case_id)

    if not config_case_path:
        filename = sample_id or case_id
        config_case_path: Path = microsalt_analysis_api.get_config_path(filename=filename)

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
    microsalt_analysis_api.process.run_command(parameters=analyse_command, dry_run=dry_run)

    if sample_id or dry_run:
        return

    microsalt_analysis_api.set_statusdb_action(case_id=case_id, action="running")
    try:
        microsalt_analysis_api.submit_trailblazer_analysis(case_id=case_id)
    except Exception as e:
        LOG.warning(
            "Trailblazer warning: Could not track analysis progress for case %s! %s",
            case_id,
            e.__class__.__name__,
        )


@microsalt.command()
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def store(context: click.Context, unique_id: str):
    """Store microSALT results in Housekeeper for given case"""
    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]

    case_obj = microsalt_analysis_api.db.family(unique_id)
    if not case_obj:
        LOG.error("Please provide a valid case id!")
        raise click.Abort
    try:
        microsalt_analysis_api.store_microbial_analysis_housekeeper(case_id=unique_id)
        microsalt_analysis_api.store_microbial_analysis_statusdb(case_id=unique_id)
        microsalt_analysis_api.set_statusdb_action(case_id=unique_id, action=None)
    except Exception as error:
        microsalt_analysis_api.db.rollback()
        microsalt_analysis_api.hk.rollback()
        LOG.error(
            "Error storing deliverables for case %s - %s", unique_id, error.__class__.__name__
        )
        raise


@microsalt.command()
@ARGUMENT_UNIQUE_IDENTIFIER
@OPTION_DRY_RUN
@OPTION_TICKET
@OPTION_SAMPLE
@click.pass_context
def start(context: click.Context, ticket: bool, sample: bool, unique_id: str, dry_run: bool):
    """Start whole microSALT workflow by providing case, ticket or sample id"""
    LOG.info("Starting Microsalt workflow for %s", unique_id)
    context.invoke(link, ticket=ticket, sample=sample, unique_id=unique_id)
    context.invoke(config_case, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)
    context.invoke(run, ticket=ticket, sample=sample, unique_id=unique_id, dry_run=dry_run)


@microsalt.command("store-available")
@OPTION_DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool):
    """Store all finished analyses in Housekeeper"""
    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]
    exit_code: int = EXIT_SUCCESS

    for case_obj in microsalt_analysis_api.get_deliverables_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        if dry_run:
            continue
        try:
            context.invoke(store, unique_id=case_obj.internal_id)
        except Exception:
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort


@microsalt.command("start-available")
@OPTION_DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool):
    """Start whole microSALT workflow for all newly sequenced cases"""
    microsalt_analysis_api: MicrosaltAnalysisAPI = context.obj["microsalt_analysis_api"]
    exit_code: int = EXIT_SUCCESS
    for case_obj in microsalt_analysis_api.db.cases_to_analyze(pipeline=Pipeline.MICROSALT):
        if dry_run:
            LOG.info("Would have started workflow for case %s", case_obj.internal_id)
            continue
        try:
            context.invoke(start, unique_id=case_obj.internal_id)
        except Exception as error:
            LOG.error(
                "Error when starting analysis for case %s - %s",
                case_obj.internal_id,
                error.__class__.__name__,
            )
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort
