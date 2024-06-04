"""CLI support to create config and/or start Jasen."""

import logging

import click

from cg.cli.utils import click_context_setting_max_content_width
from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.jasen import JasenAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(
    invoke_without_command=True, context_settings=click_context_setting_max_content_width()
)
@click.pass_context
def jasen(context: click.Context) -> None:
    """GMS/Jasen analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = JasenAnalysisAPI(config=context.obj)
