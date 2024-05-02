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

# -------------------------------------------------------
# Checking through the Tomte config-case PR:
# https://github.com/Clinical-Genomics/cg/pull/3046/files
# -------------------------------------------------------
# [x] Add JASEN dir in conftest_config() (in tests/conftest.py)
# [x] Create conda env for jasen
# [x] Add JASEN fixtures to tests/conftest.py
# [x] Add JASEN to test_config_case_without_options()
# [ ] Add JASEN to test_config_case_with_missing_case()
# [ ] Add JASEN to test_config_case_without_samples()
# [ ] Add JASEN to test_config_case_default_parameters()
# [ ] Add JASEN to test_config_case_dry_run()
# [ ] Implement config models in cg/models/cg_config.py
# [ ] Add SampleSheet classes in cg/models/jasen/jasen.py
# -------------------------------------------------------
