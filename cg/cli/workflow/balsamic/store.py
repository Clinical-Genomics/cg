"""Click commands to store balsamic analyses"""

import logging
import click

from cg.apps import hk, tb
from cg.meta.store.balsamic import gather_files_and_bundle_in_housekeeper

from cg.store import Store

from cg.exc import AnalysisNotFinishedError, AnalysisDuplicationError
from housekeeper.exc import VersionIncludedError

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["tb_api"] = tb.TrailblazerAPI(context.obj)
    context.obj["hk_api"] = hk.HousekeeperAPI(context.obj)


@store.command()
@click.argument("case_id")
@click.argument("config-stream", type=click.File("r"))
@click.pass_context
def analysis(context, case_id, config_stream):
    """Store a finished analysis in Housekeeper."""

    status = context.obj["db"]
    case_obj = status.family(case_id)

    if not case_obj:
        click.echo(click.style(f"Case {case_id} not found", fg="red"))
        context.abort()

    hk_api = context.obj["hk_api"]

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_stream, hk_api, status, case_obj
        )
    except AnalysisNotFinishedError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()
    except FileNotFoundError as error:
        click.echo(click.style(f"missing file: {error.args[0]}", fg="red"))
        context.abort()
    except AnalysisDuplicationError as error:
        click.echo(click.style("analysis version already added", fg="yellow"))
        context.abort()
    except VersionIncludedError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()

    status.add_commit(new_analysis)
    click.echo(click.style("included files in Housekeeper", fg="green"))
