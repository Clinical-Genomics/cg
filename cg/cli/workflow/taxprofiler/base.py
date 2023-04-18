"""CLI support to create config and/or start TAXPROFILER."""

import logging

import click
from pydantic import ValidationError

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.commands import link
from cg.cli.workflow.nextflow.options import (
    OPTION_CONFIG,
    OPTION_LOG,
    OPTION_PARAMS_FILE,
    OPTION_PROFILE,
    OPTION_REVISION,
    OPTION_STUB,
    OPTION_TOWER,
    OPTION_USE_NEXTFLOW,
    OPTION_WORKDIR,
)

# from cg.cli.workflow.taxprofiler.options import OPTION_FROM_START, OPTION_STRANDEDNESS
from cg.cli.workflow.tower.options import OPTION_COMPUTE_ENV
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN, CaseActions, MetaApis
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def taxprofiler(context: click.Context) -> None:
    """nf-core/taxprofiler analysis workflow."""
    AnalysisAPI.get_help(context)

    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TaxprofilerAnalysisAPI(
        config=context.obj,
    )


taxprofiler.add_command(link)
# taxprofiler.add_command(resolve_compression)
