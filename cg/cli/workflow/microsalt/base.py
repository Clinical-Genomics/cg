"""CLI support to start microsalt"""

import json
import logging
from pathlib import Path
from typing import Any

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.store import Store
from cg.constants import Pipeline, EXIT_SUCCESS, EXIT_FAIL

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
ARGUMENT_UNIQUE_IDENTIFIER = click.argument(
    "unique_id",
    required=True,
)


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
        config=context.obj["microsalt"],
    )
    context.obj["microsalt_analysis_api"] = microsalt_analysis_api


@microsalt.command()
@OPTION_TICKET
@OPTION_SAMPLE
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def link(context: click.Context, ticket: bool, sample: bool, unique_id: Any):
    """Link microbial FASTQ files for a SAMPLE_ID"""

    microsalt_analysis_api = context.obj["microsalt_analysis_api"]

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
def config_case(context: click.Context, dry_run: bool, ticket: bool, sample: bool, unique_id: Any):
    """ Create a config file on case level for microSALT """

    microsalt_analysis_api = context.obj["microsalt_analysis_api"]

    case_id, sample_id = microsalt_analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )

    sample_objs = microsalt_analysis_api.get_samples(case_id=case_id, sample_id=sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        raise click.Abort

    parameters = [microsalt_analysis_api.get_parameters(sample_obj) for sample_obj in sample_objs]

    filename = sample_id or case_id
    outfilename = Path(microsalt_analysis_api.queries_path, filename).with_suffix(".json")
    if dry_run:
        print(json.dumps(parameters, indent=4, sort_keys=True))
        return

    with open(outfilename, "w") as outfile:
        json.dump(parameters, outfile, indent=4, sort_keys=True)
    LOG.info("Saved config %s", outfilename)


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
    """ Start microSALT with an order_id """

    microsalt_analysis_api = context.obj["microsalt_analysis_api"]

    case_id, sample_id = microsalt_analysis_api.resolve_case_sample_id(
        sample=sample, ticket=ticket, unique_id=unique_id
    )

    fastq_path = Path(microsalt_analysis_api.root_dir, "fastq", case_id)

    if not config_case_path:
        filename = sample_id or case_id
        config_case_path = Path(microsalt_analysis_api.queries_path, filename).with_suffix(".json")

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

    if not sample_id and not dry_run:
        microsalt_analysis_api.set_statusdb_action(case_id=case_id, action="running")


@microsalt.command()
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def store(context: click.Context, unique_id: str):
    microsalt_analysis_api = context.obj["microsalt_analysis_api"]

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
@OPTION_TICKET
@OPTION_SAMPLE
@click.pass_context
def start(context: click.Context, ticket: bool, sample: bool, unique_id: str):
    LOG.info("Starting Microsalt workflow for %s", unique_id)
    context.invoke(link, ticket=ticket, sample=sample, unique_id=unique_id)
    context.invoke(config_case, ticket=ticket, sample=sample, unique_id=unique_id)
    context.invoke(run, ticket=ticket, sample=sample, unique_id=unique_id)


@microsalt.command("store-available")
@click.pass_context
def store_available(context: click.Context):
    microsalt_analysis_api = context.obj["microsalt_analysis_api"]
    exit_code = EXIT_SUCCESS

    for case_obj in microsalt_analysis_api.get_deliverables_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
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
    microsalt_analysis_api = context.obj["microsalt_analysis_api"]
    exit_code = EXIT_SUCCESS
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
