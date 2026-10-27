import logging
from typing import cast

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.nf_analysis import OPTION_RESUME, OPTION_REVISION
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def trana_16s():
    """gms/Trana-16S analysis workflow"""
    pass


@trana_16s.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str):
    """
    Configure a trana_16s case so that it is ready to be run.

    \b
    Creates the following files in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.TRANA_16S))
    configurator.configure(case_id=case_id)


@trana_16s.command()
@OPTION_REVISION
@OPTION_RESUME
@ARGUMENT_CASE_ID
@click.pass_obj
def run(cg_config: CGConfig, case_id: str, resume: bool, revision: str | None):
    """
    Run a preconfigured Trana 16S case.

    \b
    Assumes that the following files exist in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TRANA_16S
    )
    analysis_starter.run(case_id=case_id, resume=resume, revision=revision)


@trana_16s.command()
@OPTION_REVISION
@ARGUMENT_CASE_ID
@click.pass_obj
def start(cg_config: CGConfig, case_id: str, revision: str | None):
    """
    Start a Trana 16S case.

    \b
    Configures the case and writes the following files:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    and submits the job to the Seqera Platform.
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TRANA_16S
    )
    analysis_starter.start(case_id=case_id, revision=revision)


@trana_16s.command()
@click.pass_obj
def start_available(cg_config: CGConfig) -> None:
    """Starts all available Trana 16S cases."""
    LOG.info("Starting trana 16s workflow for all available cases.")
    analysis_starter = AnalysisStarterFactory(cg_config).get_analysis_starter_for_workflow(
        Workflow.TRANA_16S
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
