"""CLI support to create config and/or start Jasen."""

import logging

import click

from cg.cli.workflow.nf_analysis import (
    config_case,
)
from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.jasen import JasenAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def jasen(context: click.Context) -> None:
    """GMS/Jasen analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = JasenAnalysisAPI(config=context.obj)

jasen.add_command(config_case)
