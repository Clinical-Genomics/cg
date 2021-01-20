"""This script tests the cli methods to set families to status-db"""

from cg.cli.delete.case import case
from cg.store import Store

SUCCESS = 0


def test_delete_case_without_options(cli_runner, base_context, base_store: Store, helpers):
    """Test to delete a case using only the required arguments"""
    # GIVEN a database with a case
    case_id = helpers.add_family(base_store).internal_id
    assert base_store.Family.query.count() == 1

    # WHEN deleting a case
    result = cli_runner.invoke(case, obj=base_context)

    # THEN then it should abort
    assert result.exit_code != SUCCESS


def test_delete_case_bad_case(cli_runner, base_context):
    """Test to delete a case using a non-existing case """
    # GIVEN an empty database

    # WHEN deleting a case
    case_id = "dummy_name"
    result = cli_runner.invoke(case, [case_id], obj=base_context)

    # THEN then it should complain on missing case
    print(result.output)
    assert result.exit_code != SUCCESS


def test_delete_case_without_links(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case can delete a case without links"""
    # GIVEN a database with a case
    case_obj = helpers.add_family(base_store)
    case_id = case_obj.internal_id
    assert not case_obj.links

    # WHEN deleting a case

    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then it should have been deleted
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 0


def test_delete_case_with_analysis(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case can't delete a case with analysis"""
    # GIVEN a database with a case with an analysis
    analysis_obj = helpers.add_analysis(base_store)
    case_id = analysis_obj.family.internal_id

    # WHEN deleting a case

    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then it should not have been deleted
    assert result.exit_code != SUCCESS
    assert base_store.Family.query.count() == 1


def test_delete_case_with_dry_run(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete the case in dry-run mode """
    # GIVEN a database with a case
    case_obj = helpers.add_family(base_store)
    case_id = case_obj.internal_id
    assert not case_obj.links

    # WHEN deleting a case

    result = cli_runner.invoke(case, [case_id, "--yes", "--dry-run"], obj=base_context)

    # THEN then it should not have been deleted
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1


def test_delete_case_without_yes(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete the case in dry-run mode """
    # GIVEN a database with a case
    case_obj = helpers.add_family(base_store)
    case_id = case_obj.internal_id
    assert not case_obj.links

    # WHEN deleting a case

    result = cli_runner.invoke(case, [case_id], obj=base_context)

    # THEN then it should not have been deleted
    assert result.exit_code != SUCCESS
    assert base_store.Family.query.count() == 1


def test_delete_case_with_links(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case can delete a case without links"""
    # GIVEN a database with a case
    case_obj = helpers.add_family(base_store)
    case_id = case_obj.internal_id
    sample = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, family=case_obj, sample=sample)
    assert base_store.Family.query.count() > 0
    assert base_store.FamilySample.query.count() > 0
    assert base_store.Sample.query.count() > 0

    # WHEN deleting a case with links
    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then it should have been deleted
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 0
    assert base_store.FamilySample.query.count() == 0
    assert base_store.Sample.query.count() == 0
