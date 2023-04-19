"""This script tests the cli methods to get samples in status-db"""
from typing import List

from cg.cli.get import get
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from cg.store.models import Flowcell, Sample, Family
from tests.store_helpers import StoreHelpers


def test_get_sample_bad_sample(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a sample using a non-existing sample-id"""
    # GIVEN an empty database

    # WHEN getting a sample
    name = "dummy_name"
    result = cli_runner.invoke(get, ["sample", name], obj=base_context)

    # THEN it should warn about missing sample id instead of getting a sample
    # it will not fail since the API accepts multiple samples
    assert result.exit_code == 0


def test_get_sample_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a sample using only the required argument"""
    # GIVEN a database with a sample
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    assert disk_store._get_query(table=Sample).count() == 1

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert sample_id in result.output


def test_get_samples_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get several samples using only the required arguments"""
    # GIVEN a database with two samples
    sample_id1 = "1"
    helpers.add_sample(store=disk_store, internal_id=sample_id1)
    sample_id2 = "2"
    helpers.add_sample(store=disk_store, internal_id=sample_id2)

    assert disk_store._get_query(table=Sample).count() == 2

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id1, sample_id2], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert sample_id1 in result.output
    assert sample_id2 in result.output


def test_get_sample_output(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the data of the sample"""
    # GIVEN a database with a sample with data
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    name = sample.name
    customer_id = sample.customer.internal_id
    application_tag = sample.application_version.application.tag
    state = sample.state
    priority_human = sample.priority_human

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert sample_id in result.output
    assert name in result.output
    assert customer_id in result.output
    assert application_tag in result.output
    assert state in result.output
    assert priority_human in result.output


def test_get_sample_external_false(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the external-value of the sample"""
    # GIVEN a database with a sample with data
    sample = helpers.add_sample(disk_store, is_external=False)
    sample_id = sample.internal_id
    is_external_false = "No"
    is_external_true = "Yes"

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert is_external_false in result.output
    assert is_external_true not in result.output


def test_get_sample_external_true(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the output has the external-value of the sample"""
    # GIVEN a database with a sample with data
    sample = helpers.add_sample(disk_store, is_external=True)
    sample_id = sample.internal_id
    is_external_false = "No"
    is_external_true = "Yes"

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id], obj=base_context)

    # THEN it should have been get
    assert result.exit_code == 0
    assert is_external_true in result.output
    assert is_external_false not in result.output


def test_get_sample_no_cases_without_case(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --no-cases flag works without cases."""
    # GIVEN a database with a sample without related samples
    sample: Sample = helpers.add_sample(disk_store)

    # WHEN getting a sample with the --no-families flag
    result = cli_runner.invoke(get, ["sample", sample.internal_id, "--no-cases"], obj=base_context)

    # THEN everything is fine
    assert result.exit_code == EXIT_SUCCESS


def test_get_sample_no_cases_with_case(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --no-cases flag does not show case info"""
    # GIVEN a database with a sample with related samples
    case: Family = helpers.add_case(disk_store)
    sample: Sample = helpers.add_sample(disk_store)
    helpers.add_relationship(disk_store, sample=sample, case=case)

    # WHEN getting a sample with the --no-families flag
    result = cli_runner.invoke(get, ["sample", sample.internal_id, "--no-cases"], obj=base_context)

    # THEN all related cases should be listed in the output
    assert result.exit_code == EXIT_SUCCESS
    for family_sample in disk_store._get_query(table=Sample).first().links:
        assert family_sample.family.internal_id not in result.output


def test_get_sample_cases_without_case(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --cases flag works without cases"""
    # GIVEN a database with a sample without related samples
    sample: Sample = helpers.add_sample(disk_store)
    assert not disk_store._get_query(table=Sample).first().links

    # WHEN getting a sample with the --cases flag
    result = cli_runner.invoke(get, ["sample", sample.internal_id, "--cases"], obj=base_context)

    # THEN everything is fine
    assert result.exit_code == EXIT_SUCCESS


def test_get_sample_cases_with_case(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --cases flag does show case info"""
    # GIVEN a database with a sample with related samples
    case: Family = helpers.add_case(disk_store)
    sample: Sample = helpers.add_sample(disk_store)
    helpers.add_relationship(disk_store, sample=sample, case=case)

    # WHEN getting a sample with the --families flag
    result = cli_runner.invoke(get, ["sample", sample.internal_id, "--cases"], obj=base_context)

    # THEN all related families should be listed in the output
    assert result.exit_code == EXIT_SUCCESS
    for link in disk_store._get_query(table=Sample).first().links:
        assert link.family.internal_id in result.output


def test_hide_sample_flowcells_without_flowcell(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that we can query samples and hide flow cell even when there are none."""
    # GIVEN a database with a sample without related flow cell
    sample = helpers.add_sample(disk_store)
    returned_flow_cell: List[Flowcell] = disk_store._get_query(table=Flowcell)
    assert not list(returned_flow_cell)

    # WHEN getting a sample with the --hide-flow-cell flag
    result = cli_runner.invoke(
        get, ["sample", sample.internal_id, "--hide-flow-cell"], obj=base_context
    )

    # THEN process should exit successfully
    assert result.exit_code == EXIT_SUCCESS


def test_get_sample_flowcells_with_flowcell(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test query samples and hide flow cell, ensuring that no flow cell name is in the output."""
    # GIVEN a database with a sample and a related flow cell
    flow_cell = helpers.add_flowcell(disk_store)
    sample = helpers.add_sample(disk_store, flowcell=flow_cell)
    returned_flow_cell: Flowcell = disk_store.get_flow_cell_by_name(flow_cell_name=flow_cell.name)
    assert sample in returned_flow_cell.samples

    # WHEN getting a sample with the --hide-flow-cell flag
    result = cli_runner.invoke(
        get, ["sample", sample.internal_id, "--hide-flow-cell"], obj=base_context
    )

    # THEN the process should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the related flow cell should be listed in the output
    assert flow_cell.name not in result.output
