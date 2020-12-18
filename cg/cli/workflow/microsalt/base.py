"""CLI support to start microsalt"""

import json
import logging
from pathlib import Path
from typing import Any

import click

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.store import Store
from cg.utils.commands import Process

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
    help="Unique identifier for case/ticket/sample which it to be analyzed",
    required=True,
)


@click.group("microsalt", invoke_without_command=True)
@click.pass_context
def microsalt(context: click.Context):
    """Microbial workflow"""
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

    if ticket and sample:
        LOG.error("Flags -t and -s are mutually exclusive!")
        raise click.Abort

    if ticket:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_ticket(unique_id)

    elif sample:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_sample(unique_id)

    else:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_case(unique_id)

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

    if ticket and sample:
        LOG.error("Flags -t and -s are mutually exclusive!")
        raise click.Abort

    if ticket:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_ticket(unique_id)

    elif sample:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_sample(unique_id)

    else:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_case(unique_id)

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


@microsalt.command()
@OPTION_DRY_RUN
@click.option(
    "-c",
    "--config-case",
    "config_case_path",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="optionally change the config-case",
)
@click.argument("ticket", type=int)
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

    if ticket and sample:
        LOG.error("Flags -t and -s are mutually exclusive!")
        raise click.Abort

    if ticket:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_ticket(unique_id)

    elif sample:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_sample(unique_id)

    else:
        case_id, sample_id = microsalt_analysis_api.get_case_id_from_case(unique_id)

    fastq_path = Path(microsalt_analysis_api.root_dir, "fastq", case_id)

    if config_case_path:
        config_case_path = Path(config_case_path)
    else:
        filename = sample_id or case_id
        config_case_path = Path(microsalt_analysis_api.queries_path, filename).with_suffix(".json")

    analyse_command = [
        "analyse",
        config_case_path.absolute().as_posix(),
        "--input",
        fastq_path.absolute().as_posix(),
    ]
    microsalt_analysis_api.process.run_command(parameters=analyse_command, dry_run=dry_run)

    if not sample_id and not dry_run:
        microsalt_analysis_api.set_statusdb_action(case_id=case_id, action="running")


microsalt.add_command(store_cmd)
