"""This script tests the cli methods to get analysis in status-db"""

from cg.cli.get import get
from cg.constants import RETURN_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_get_family_bad_case(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a analysis using a non-existing analysis-id"""
    # GIVEN an empty database

    # WHEN getting a analysis
    name = "dummy_name"
    result = cli_runner.invoke(get, ["family", name], obj=base_context)

    # THEN it should error about missing case instead of getting a case
    assert result.exit_code != RETURN_SUCCESS


def test_get_family_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a case using only the required argument"""
    # GIVEN a database with a analysis
    family: models.Family = helpers.add_case(disk_store)
    internal_id = family.internal_id
    assert disk_store.Family.query.count() == 1

    # WHEN getting a analysis
    result = cli_runner.invoke(get, ["family", internal_id], obj=base_context)

    # THEN it should have been gotten
    assert result.exit_code == RETURN_SUCCESS
    assert internal_id in result.output
