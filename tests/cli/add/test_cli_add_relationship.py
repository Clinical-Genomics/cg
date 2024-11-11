"""This script tests the cli methods to add families to status-db"""

from click.testing import CliRunner

from cg.cli.add import add
from cg.constants import EXIT_FAIL
from cg.constants.subject import Sex
from cg.models.cg_config import CGConfig
from cg.store.models import CaseSample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_add_relationship_required(cli_runner: CliRunner, base_context: CGConfig, helpers):
    """Test to add a relationship using only the required arguments"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    result = cli_runner.invoke(
        add, ["relationship", case_id, sample_id, "-s", status], obj=base_context
    )

    # THEN it should be added
    assert result.exit_code == 0
    family_sample_query = disk_store._get_query(table=CaseSample)

    assert family_sample_query.count() == 1
    assert family_sample_query.first().case.internal_id == case_id
    assert family_sample_query.first().sample.internal_id == sample_id


def test_add_relationship_bad_sample(cli_runner: CliRunner, base_context: CGConfig, helpers):
    """Test to add a relationship using a non-existing sample"""
    # GIVEN an empty database
    disk_store: Store = base_context.status_db
    # WHEN adding a relationship
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    sample_id = "dummy_sample"
    status = "affected"
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ],
        obj=base_context,
    )

    # THEN it should complain on missing sample instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_bad_family(cli_runner: CliRunner, base_context: CGConfig, helpers):
    """Test to add a relationship using a non-existing case"""
    # GIVEN a database with a sample
    disk_store: Store = base_context.status_db
    # WHEN adding a relationship
    case_id = "dummy_family"
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    status = "affected"
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ],
        obj=base_context,
    )

    # THEN it should complain in missing case instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_bad_status(cli_runner: CliRunner, base_context: CGConfig, helpers):
    """Test that the added relationship get the status we send in"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    # WHEN adding a relationship

    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "dummy_status"

    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ],
        obj=base_context,
    )

    # THEN it should complain on bad status instead of adding a relationship
    assert result.exit_code == 2
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_mother(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship with a mother"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    mother = helpers.add_sample(disk_store, name="mother")
    mother_id = mother.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-m",
            mother_id,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == 0
    family_sample_query = disk_store._get_query(table=CaseSample)
    assert family_sample_query.count() == 1
    assert family_sample_query.first().mother.internal_id == mother_id


def test_add_relationship_bad_mother(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship using a non-existing mother"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    mother_id = "dummy_mother"
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-m",
            mother_id,
        ],
        obj=base_context,
    )

    # THEN it should not be added
    assert result.exit_code == 1
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_father(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship using a father"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    father = helpers.add_sample(disk_store, sex=Sex.MALE, name="father")
    father_id = father.internal_id

    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    status = "affected"

    # WHEN adding a relationship
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-f",
            father_id,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == 0
    family_sample_query = disk_store._get_query(table=CaseSample)
    assert family_sample_query.count() == 1
    assert family_sample_query.first().father.internal_id == father_id


def test_add_relationship_bad_father(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship using a non-existing father"""
    # GIVEN a database with a sample and an case
    disk_store: Store = base_context.status_db
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    father_id = "bad_father"
    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    status = "affected"

    # WHEN adding a relationship
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-f",
            father_id,
        ],
        obj=base_context,
    )

    # THEN it should not be added
    assert result.exit_code == 1
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_mother_not_female(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship where the mother is not female"""
    # GIVEN a database with a sample, a case, and a male sample labeled as mother
    disk_store: Store = base_context.status_db
    sample: Sample = helpers.add_sample(disk_store)
    sample_id: str = sample.internal_id

    male_mother: Sample = helpers.add_sample(disk_store, sex=Sex.MALE, name="mother")
    male_mother_id: str = male_mother.internal_id

    case: Case = helpers.add_case(disk_store)
    case_id: str = case.internal_id
    status = "affected"

    # WHEN adding a relationship with a male mother
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-m",
            male_mother_id,
        ],
        obj=base_context,
    )

    # THEN it should fail because the mother is not female
    assert result.exit_code == EXIT_FAIL
    assert disk_store._get_query(table=CaseSample).count() == 0


def test_add_relationship_father_not_male(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a relationship where the father is not male"""
    # GIVEN a database with a sample, a case, and a female sample labeled as father
    disk_store: Store = base_context.status_db
    sample: Sample = helpers.add_sample(disk_store)
    sample_id: str = sample.internal_id

    female_father: Sample = helpers.add_sample(disk_store, sex=Sex.FEMALE, name="father")
    female_father_id: str = female_father.internal_id

    case: Case = helpers.add_case(disk_store)
    case_id: str = case.internal_id
    status = "affected"

    # WHEN adding a relationship with a female father
    result = cli_runner.invoke(
        add,
        [
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-f",
            female_father_id,
        ],
        obj=base_context,
    )

    # THEN it should fail because the father is not male
    assert result.exit_code == EXIT_FAIL
    assert disk_store._get_query(table=CaseSample).count() == 0
