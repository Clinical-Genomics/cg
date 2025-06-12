"""Commands to start MIP rare disease DNA workflow."""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    ensure_illumina_runs_on_disk,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.cli.workflow.mip.base import (
    config_case,
    managed_variants,
    panel,
    run,
    start,
    start_available,
)
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(
    "mip-dna",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.pass_context
def mip_dna(
    context: click.Context,
):
    """Rare disease DNA workflow"""
    AnalysisAPI.get_help(context)

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(config=context.obj)


for sub_cmd in [
    config_case,
    ensure_illumina_runs_on_disk,
    link,
    managed_variants,
    panel,
    resolve_compression,
    run,
    start,
    start_available,
    store,
    store_available,
]:
    mip_dna.add_command(sub_cmd)
