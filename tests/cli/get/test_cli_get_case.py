"""Test CLI functions to get analysis in the Status database."""

from cg.cli.get import get
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from cg.store.models import Family
from tests.store_helpers import StoreHelpers


def test_get_case_bad_case(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a analysis using a non-existing analysis id."""
    # GIVEN an empty database

    # WHEN getting a analysis
    result = cli_runner.invoke(get, ["case", "dummy_name"], obj=base_context)

    # THEN it should error about missing case instead of getting a case
    assert result.exit_code != EXIT_SUCCESS


def test_get_case_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a case using only the required argument."""
    # GIVEN a database with a analysis
    family: Family = helpers.add_case(disk_store)

    # WHEN getting a analysis
    result = cli_runner.invoke(get, ["case", family.internal_id], obj=base_context)

    # THEN it should have been returned
    assert result.exit_code == EXIT_SUCCESS
    assert family.internal_id in result.output
