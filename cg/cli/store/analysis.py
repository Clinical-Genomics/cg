import logging
from pathlib import Path

import click

from cg.apps.hermes.hermes_api import HermesApi
from cg.constants import Pipeline
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.command(name="analysis")
@click.argument("infile", type=click.Path(exists=True))
@click.option(
    "--pipeline",
    help="Specify what pipeline that produced the deliverables",
    required=True,
    type=EnumChoice(Pipeline),
)
@click.pass_context
def store_analysis_cmd(context, pipeline: Pipeline, infile: Path):
    """Command for storing analysis results in housekeeper"""
    LOG.info("Store analysis result in Housekeeper")
    hermes_api = HermesApi(config=context.obj, pipeline=pipeline)
    from pprint import pprint as pp

    pp(hermes_api.convert_deliverables(deliverables_file=infile).dict())
