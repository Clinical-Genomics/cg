import logging
from pathlib import Path

import click

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import AnalysisUploadError
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
    try:
        upload_api.upload_deliverables(deliverables_file=infile, pipeline="fluffy")
    except AnalysisUploadError as err:
        LOG.warning(err)
        raise click.Abort
