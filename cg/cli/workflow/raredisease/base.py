"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_DRY
from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """NF-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(
        config=context.obj,
    )


@raredisease.command("panel")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write aggregated gene panel file exported from Scout."""

    analysis_api: RarediseaseAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    bed_lines: list[str] = analysis_api.get_gene_panel(case_id=case_id)
    if dry_run:
        for bed_line in bed_lines:
            click.echo(bed_line)
        return
    analysis_api.write_panel(case_id=case_id, content=bed_lines)
