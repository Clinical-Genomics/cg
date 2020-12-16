import logging
from pathlib import Path

import click

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import ANALYSIS_TYPES, Pipeline
from cg.meta.upload.analysis import UploadAnalysisApi

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def analysis(context):
    """Command for storing analysis results in housekeeper"""
    LOG.info("Running store cg store analysis")

    hermes_api = HermesApi(config=context.obj)
    housekeeper_api = HousekeeperAPI(context.obj)
    context.obj["upload_api"] = UploadAnalysisApi(hk_api=housekeeper_api, hermes_api=hermes_api)


@analysis.command(name="fluffy")
@click.pass_context
@click.argument("infile", type=click.Path(exists=True))
def fluffy_cmd(context, infile: Path):
    upload_api = context.obj["upload_api"]
    upload_api.upload_deliverables(deliverables_file=infile, pipeline="fluffy")


@analysis.command(name="balsamic")
@click.pass_context
@click.argument("infile", type=click.Path(exists=True))
@click.option(
    "--analysis-type",
    help="Specify the analysis type that was used",
    type=click.Choice(ANALYSIS_TYPES),
    required=True,
)
def balsamic_cmd(context, infile: Path, analysis_type: str):
    upload_api = context.obj["upload_api"]
