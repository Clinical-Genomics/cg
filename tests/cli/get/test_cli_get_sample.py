"""This script tests the cli methods to get samples in status-db"""

from cg.cli.get import get
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_get_sample_bad_sample(cli_runner: CliRunner, base_context: CGConfig):
    """Test to get a sample using a non-existing sample-id """
    # GIVEN an empty database

    # WHEN getting a sample
    name = "dummy_name"
    result = cli_runner.invoke(get, ["sample", name], obj=base_context)

    # THEN then it should warn about missing sample id instead of getting a sample
    # it will not fail since the API accepts multiple samples
    assert result.exit_code == 0


def test_get_sample_required(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test to get a sample using only the required argument"""
    # GIVEN a database with a sample
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    assert disk_store.Sample.query.count() == 1

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id], obj=base_context)

    # THEN then it should have been get
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

    assert disk_store.Sample.query.count() == 2

    # WHEN getting a sample
    result = cli_runner.invoke(get, ["sample", sample_id1, sample_id2], obj=base_context)

    # THEN then it should have been get
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

    # THEN then it should have been get
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

    # THEN then it should have been get
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

    # THEN then it should have been get
    assert result.exit_code == 0
    assert is_external_true in result.output
    assert is_external_false not in result.output


def test_get_sample_no_families_without_family(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --no-families flag works without families"""
    # GIVEN a database with a sample without related samples
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    assert not disk_store.Sample.query.first().links

    # WHEN getting a sample with the --no-families flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--no-families"], obj=base_context)

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_no_families_with_family(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --no-families flag doesn't show case info"""
    # GIVEN a database with a sample with related samples
    case = helpers.add_case(disk_store)
    sample = helpers.add_sample(disk_store)
    link = helpers.add_relationship(disk_store, sample=sample, case=case)
    assert link in disk_store.Sample.query.first().links
    sample_id = sample.internal_id

    # WHEN getting a sample with the --no-families flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--no-families"], obj=base_context)

    # THEN all related families should be listed in the output
    assert result.exit_code == 0
    for link in disk_store.Sample.query.first().links:
        assert link.family.internal_id not in result.output


def test_get_sample_families_without_family(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --families flag works without families"""
    # GIVEN a database with a sample without related samples
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    assert not disk_store.Sample.query.first().links

    # WHEN getting a sample with the --families flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--families"], obj=base_context)

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_families_with_family(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that the --families flag does show case info"""
    # GIVEN a database with a sample with related samples
    case = helpers.add_case(disk_store)
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    helpers.add_relationship(disk_store, sample=sample, case=case)
    assert disk_store.Sample.query.first().links

    # WHEN getting a sample with the --families flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--families"], obj=base_context)

    # THEN all related families should be listed in the output
    assert result.exit_code == 0
    for link in disk_store.Sample.query.first().links:
        assert link.family.internal_id in result.output


def test_get_sample_flowcells_without_flowcell(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that we can query samples for flowcells even when there are none"""
    # GIVEN a database with a sample without related flowcells
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    assert not disk_store.Flowcell.query.first()

    # WHEN getting a sample with the --flowcells flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--flowcells"], obj=base_context)

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_flowcells_with_flowcell(
    cli_runner: CliRunner, base_context: CGConfig, disk_store: Store, helpers: StoreHelpers
):
    """Test that we can query samples for flowcells and that the flowcell name is in the output"""
    # GIVEN a database with a sample and a related flowcell
    flowcell = helpers.add_flowcell(disk_store)
    sample = helpers.add_sample(disk_store, flowcell=flowcell)
    assert flowcell in disk_store.Sample.query.first().flowcells
    sample_id = sample.internal_id

    # WHEN getting a sample with the --flowcells flag
    result = cli_runner.invoke(get, ["sample", sample_id, "--flowcells"], obj=base_context)

    # THEN the related flowcell should be listed in the output
    assert result.exit_code == 0
    for flowcell in disk_store.Sample.query.first().flowcells:
        assert flowcell.name in result.output
