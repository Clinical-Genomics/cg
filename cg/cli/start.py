import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter


@click.command(context_settings=CLICK_CONTEXT_SETTINGS, name="start")
@click.pass_context
@click.argument("case_id")
def start(context: CGConfig, case_id: str):
    """Start the analysis for the given case."""
    starter_factory = AnalysisStarterFactory(context)
    analysis_starter: AnalysisStarter = starter_factory.get_analysis_starter(case_id)
    analysis_starter.start(case_id)
