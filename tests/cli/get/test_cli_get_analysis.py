"""This script tests the cli methods to get analysis in status-db"""

from cg.cli.get import get
from cg.constants import RETURN_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Analysis
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_get_analysis_bad_case(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a analysis using a non-existing analysis-id"""
    # GIVEN an empty database

    # WHEN getting a analysis
    name = "dummy_name"
    result = cli_runner.invoke(get, ["analysis", name], obj=base_context)

    # THEN it should error about missing case instead of getting a analysis
    assert result.exit_code != RETURN_SUCCESS


def test_get_analysis_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a analysis using only the required argument"""
    # GIVEN a database with an analysis
    analysis: Analysis = helpers.add_analysis(disk_store, pipeline_version="9.3")
    internal_id = analysis.family.internal_id
    assert disk_store._get_query(table=Analysis).count() == 1

    # WHEN getting a analysis
    result = cli_runner.invoke(get, ["analysis", internal_id], obj=base_context)

    # THEN it should have been gotten
    assert result.exit_code == RETURN_SUCCESS
    assert str(analysis.started_at) in result.output
    assert analysis.pipeline in result.output
    assert analysis.pipeline_version in result.output
