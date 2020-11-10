"""CLI support to start microsalt"""

import json
import logging
from pathlib import Path

import click

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.microsalt.fastq import FastqHandler
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.store import Store
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


@click.group("microsalt", invoke_without_command=True)
@click.option("-d", "--dry-run", is_flag=True, help="print to console")
@click.option("-t", "--ticket", help="include all microbial samples for a ticket")
@click.pass_context
def microsalt(context: click.Context, ticket: str, dry_run: bool):
    """Microbial workflow"""
    context.obj["status_db"] = Store(context.obj["database"])
    hk_api = HousekeeperAPI(context.obj)
    lims_api = LimsAPI(context.obj)
    analysis_api = MicrosaltAnalysisAPI(
        db=context.obj["status_db"],
        hk_api=hk_api,
        lims_api=lims_api,
        fastq_handler=FastqHandler(context.obj),
        config=context.obj["microsalt"],
    )
    context.obj["microsalt_analysis_api"] = analysis_api

    if context.invoked_subcommand:
        return

    if not ticket:
        LOG.error("Please provide a ticket")
        context.abort()

    if not analysis_api.has_flowcells_on_disk(ticket=ticket):
        LOG.warning(
            f"Ticket {ticket} not ready to run, requesting flowcells from long term storage!",
        )
        analysis_api.request_removed_flowcells(ticket=ticket)
        return

    # execute the analysis!
    context.invoke(config_case, ticket=ticket, dry_run=dry_run)
    context.invoke(link, ticket=ticket, dry_run=dry_run)
    context.invoke(run, ticket=ticket, dry_run=dry_run)


@microsalt.command()
@click.option("-d", "--dry-run", is_flag=True, help="only print to console")
@click.option("-t", "--ticket", help="link all microbial samples for a ticket")
@click.argument("sample_id", required=False)
@click.pass_context
def link(context: click.Context, dry_run: bool, ticket: str, sample_id: str):
    """Link microbial FASTQ files for a SAMPLE_ID"""

    analysis_api = context.obj["microsalt_analysis_api"]

    if not any([ticket, sample_id]):
        LOG.error("provide ticket and/or sample")
        context.abort()

    if dry_run:
        return

    analysis_api.link_samples(ticket=ticket, sample_id=sample_id)


@microsalt.command("config-case")
@click.option("-d", "--dry-run", is_flag=True, help="print config to console")
@click.option("-t", "--ticket", help="create config-case all microbial samples for an order")
@click.argument("sample_id", required=False)
@click.pass_context
def config_case(context: click.Context, dry_run: bool, ticket: int, sample_id: str):
    """ Create a config file on case level for microSALT """

    if not ticket and not sample_id:
        LOG.error("Provide ticket and/or sample")
        context.abort()

    sample_objs = context.obj["microsalt_analysis_api"].get_samples(ticket, sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        context.abort()

    parameters = [
        context.obj["microsalt_analysis_api"].get_parameters(sample_obj)
        for sample_obj in sample_objs
    ]

    filename = str(ticket) if ticket else sample_id
    outfilename = (Path(context.obj["microsalt"]["queries_path"]) / filename).with_suffix(".json")
    if dry_run:
        print(json.dumps(parameters, indent=4, sort_keys=True))
        return

    with open(outfilename, "w") as outfile:
        json.dump(parameters, outfile, indent=4, sort_keys=True)


@microsalt.command()
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
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
def run(context: click.Context, dry_run: bool, config_case_path: click.Path, ticket: int):
    """ Start microSALT with an order_id """

    microbial_api = context.obj["microsalt_analysis_api"]

    microsalt_bin = context.obj["microsalt"]["binary_path"]
    microsalt_env = context.obj["microsalt"]["conda_env"]
    fastq_path = Path(context.obj["microsalt"]["root"]) / "fastq" / str(ticket)

    if config_case_path:
        config_case_path = Path(config_case_path)
    else:
        queries_path = Path(context.obj["microsalt"]["queries_path"])
        config_case_path = (queries_path / str(ticket)).with_suffix(".json")

    process = Process(binary=microsalt_bin, environment=microsalt_env)
    analyse_command = [
        "analyse",
        str(config_case_path.absolute()),
        "--input",
        str(fastq_path.absolute()),
    ]
    process.run_command(parameters=analyse_command, dry_run=dry_run)

    if not dry_run:
        microbial_api.set_statusdb_action(name=ticket, action="running")


microsalt.add_command(store_cmd)
