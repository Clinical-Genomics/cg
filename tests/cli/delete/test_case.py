"""This script tests the cli methods to set families to status-db"""
import logging

from cg.cli.delete.case import case
from cg.store import Store

SUCCESS = 0


def test_delete_case_without_options(cli_runner, base_context, base_store: Store, helpers):
    """Test to delete a case using only the required arguments"""
    # GIVEN a database with a case
    helpers.add_case(base_store)
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
    assert result.exit_code != SUCCESS


def test_delete_case_without_links(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case can delete a case without links"""
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store)
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


def test_delete_case_with_dry_run(cli_runner, base_context, base_store: Store, helpers, caplog):
    """Test that the delete case will not delete the case in dry-run mode """
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store)
    case_id = case_obj.internal_id
    sample = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample)
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 1

    # WHEN deleting a case
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(case, [case_id, "--yes", "--dry-run"], obj=base_context)

    # THEN then it should not have been deleted
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 1
    assert "Link:" in caplog.text
    assert "Sample is linked" in caplog.text
    assert "Case:" in caplog.text
    assert " was NOT deleted due to --dry-run" in caplog.text


def test_delete_case_without_yes(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete the case in dry-run mode """
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store)
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
    case_obj = helpers.add_case(base_store)
    case_id = case_obj.internal_id
    sample = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample)
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


def test_delete_case_with_links_to_other_case(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete a sample linked to another case"""
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store, "first_case_linked_to_sample")
    case_id = case_obj.internal_id
    sample = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample)
    case_obj2 = helpers.add_case(base_store, "second_case_linked_to_sample")
    helpers.add_relationship(store=base_store, case=case_obj2, sample=sample)

    assert base_store.Family.query.count() == 2
    assert base_store.FamilySample.query.count() == 2
    assert base_store.Sample.query.count() == 1

    # WHEN deleting a case
    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then the first case should be gone with its link to the sample but not the other or
    # the sample
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 1


def test_delete_case_with_father_links(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete a sample linked to another case as father"""
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store, "first_case_linked_to_sample")
    case_id = case_obj.internal_id
    sample_father = helpers.add_sample(base_store, "father")
    sample_child = helpers.add_sample(base_store, "child")
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_father)
    case_obj2 = helpers.add_case(base_store, "second_case_linked_to_sample")
    helpers.add_relationship(
        store=base_store, case=case_obj2, sample=sample_child, father=sample_father
    )

    assert base_store.Family.query.count() == 2
    assert base_store.FamilySample.query.count() == 2
    assert base_store.Sample.query.count() == 2

    # WHEN deleting a case
    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then the first case should be gone with its link to the sample but not the other or
    # the father sample
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 2


def test_delete_mother_case(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete a sample linked to another case as mother"""
    # GIVEN a database with a mother case and a child case with the mother as mother
    case_mother = helpers.add_case(base_store, "case_mother")
    case_mother_id = case_mother.internal_id
    sample_mother = helpers.add_sample(base_store, "mother")
    sample_child = helpers.add_sample(base_store, "child")
    helpers.add_relationship(store=base_store, case=case_mother, sample=sample_mother)
    case_child = helpers.add_case(base_store, "case_child")
    helpers.add_relationship(
        store=base_store, case=case_child, sample=sample_child, mother=sample_mother
    )

    assert base_store.Family.query.count() == 2
    assert base_store.FamilySample.query.count() == 2
    assert base_store.Sample.query.count() == 2

    # WHEN deleting the mother case
    result = cli_runner.invoke(case, [case_mother_id, "--yes"], obj=base_context)

    # THEN the mother sample is not deletable
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 2


def test_delete_child_case(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will not delete a sample linked to another case as mother"""
    # GIVEN a database with a mother case and a child case with the mother as mother
    case_mother = helpers.add_case(base_store, "case_mother")
    sample_mother = helpers.add_sample(base_store, "mother")
    sample_child = helpers.add_sample(base_store, "child")
    helpers.add_relationship(store=base_store, case=case_mother, sample=sample_mother)
    case_child = helpers.add_case(base_store, "case_child")
    case_child_id = case_child.internal_id
    helpers.add_relationship(
        store=base_store, case=case_child, sample=sample_child, mother=sample_mother
    )

    assert base_store.Family.query.count() == 2
    assert base_store.FamilySample.query.count() == 2
    assert base_store.Sample.query.count() == 2

    # WHEN deleting the child case
    result = cli_runner.invoke(case, [case_child_id, "--yes"], obj=base_context)

    # THEN the child sample is deletable
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 1
    assert base_store.Sample.query.count() == 1


def test_delete_trio_case(cli_runner, base_context, base_store: Store, helpers):
    """Test that the delete case will delete a trio"""
    # GIVEN a database with a trio case
    case_obj = helpers.add_case(base_store)
    case_id = case_obj.internal_id
    sample_mother = helpers.add_sample(base_store, "mother")
    sample_father = helpers.add_sample(base_store, "father")
    sample_child = helpers.add_sample(base_store, "child")
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_mother)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_father)
    helpers.add_relationship(
        store=base_store,
        case=case_obj,
        sample=sample_child,
        mother=sample_mother,
        father=sample_father,
    )

    assert base_store.Family.query.count() == 1
    assert base_store.FamilySample.query.count() == 3
    assert base_store.Sample.query.count() == 3

    # WHEN deleting a case
    result = cli_runner.invoke(case, [case_id, "--yes"], obj=base_context)

    # THEN then the trio case should be gone
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 0
    assert base_store.FamilySample.query.count() == 0
    assert base_store.Sample.query.count() == 0
