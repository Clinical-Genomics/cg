"""CLI support to start microsalt"""

import json
import logging
from pathlib import Path
import subprocess

import click

from cg.apps import hk, lims
from cg.apps.usalt.fastq import FastqHandler
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.cli.workflow.microsalt.deliver import deliver as deliver_cmd
from cg.meta.microsalt.lims import LimsMicrosaltAPI
from cg.meta.workflow.microsalt import AnalysisAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("microsalt", invoke_without_command=True)
@click.option("-d", "--dry-run", is_flag=True, help="print to console")
@click.option("-t", "--ticket", help="include all microbial samples for a ticket")
@click.pass_context
def microsalt(context: click.Context, ticket, dry_run):
    """Microbial workflow"""
    context.obj["db"] = Store(context.obj["database"])
    hk_api = hk.HousekeeperAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)
    context.obj["api"] = AnalysisAPI(db=context.obj["db"], hk_api=hk_api, lims_api=lims_api)
    context.obj["lims_microsalt_api"] = LimsMicrosaltAPI(lims=lims_api)

    if context.invoked_subcommand is None:
        if not ticket:
            LOG.error("Please provide a ticket")
            context.abort()
        else:
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

    api = context.obj["api"]
    sample_objs = api.get_samples(ticket, sample_id)

    if not sample_objs:
        LOG.error("provide ticket and/or sample")
        context.abort()

    for sample_obj in sample_objs:
        LOG.info("%s: link FASTQ files", sample_obj.internal_id)
        if dry_run:
            continue
        api.link_sample(
            FastqHandler(context.obj),
            case=ticket,
            sample=sample_obj.internal_id,
        )


@microsalt.command("config-case")
@click.option("-d", "--dry-run", is_flag=True, help="print config to console")
@click.option("-t", "--ticket", help="create config-case all microbial samples for an order")
@click.argument("sample_id", required=False)
@click.pass_context
def config_case(context: click.Context, dry_run, ticket: int, sample_id: str):
    """ Create a config file on case level for microSALT """

    if not ticket and not sample_id:
        LOG.error("Provide ticket and/or sample")
        context.abort()

    sample_objs = context.obj["api"].get_samples(ticket, sample_id)

    if not sample_objs:
        LOG.error("No sample found for that ticket/sample_id")
        context.abort()

    parameters = [
        context.obj["lims_microsalt_api"].get_parameters(sample_obj) for sample_obj in sample_objs
    ]

    filename = str(ticket) if ticket else sample_id
    outfilename = (Path(context.obj["usalt"]["queries_path"]) / filename).with_suffix(".json")
    if dry_run:
        print(json.dumps(parameters, indent=4, sort_keys=True))
    else:
        with open(outfilename, "w") as outfile:
            json.dump(parameters, outfile, indent=4, sort_keys=True)


@microsalt.command()
@click.option("-d", "--dry-run", "dry_run", is_flag=True, help="print command to console")
@click.option("-c", "--config-case", "config_case_path", required=False, help="optionally change "
                                                                              "the config-case")
@click.argument("ticket")
@click.pass_context
def run(context, dry_run, config_case_path, ticket):
    """ Start microSALT with an order_id """

    microsalt_command = context.obj["usalt"]["binary_path"]
    command = [microsalt_command]

    if not config_case:
        queries_path = Path(context.obj["usalt"]["queries_path"])
        config_case_path = (queries_path / ticket).with_suffix(".json")

    command.extend(["--parameters", str(config_case_path)])
    if dry_run:
        print(" ".join(command))
    else:
        LOG.info("Starting microSALT! '%s'", " ".join(command))
        subprocess.run(command, shell=True, check=True)


microsalt.add_command(config_case)
microsalt.add_command(deliver_cmd)
microsalt.add_command(run)
microsalt.add_command(store_cmd)
