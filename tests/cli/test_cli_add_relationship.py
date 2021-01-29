"""This script tests the cli methods to add families to status-db"""

from cg.store import Store


def test_add_relationship_required(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using only the required arguments"""
    # GIVEN a database with a sample and an case
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().family.internal_id == case_id
    assert disk_store.FamilySample.query.first().sample.internal_id == sample_id


def test_add_relationship_bad_sample(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using a non-existing sample"""
    # GIVEN an empty database

    # WHEN adding a relationship
    db_uri = disk_store.uri
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    sample_id = "dummy_sample"
    status = "affected"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ]
    )

    # THEN then it should complain on missing sample instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_bad_family(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using a non-existing case"""
    # GIVEN a database with a sample

    # WHEN adding a relationship
    db_uri = disk_store.uri
    case_id = "dummy_family"
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    status = "affected"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ]
    )

    # THEN then it should complain in missing case instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_bad_status(invoke_cli, disk_store: Store, helpers):
    """Test that the added relationship get the status we send in"""
    # GIVEN a database with a sample and an case

    # WHEN adding a relationship
    db_uri = disk_store.uri

    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "dummy_status"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
        ]
    )

    # THEN then it should complain on bad status instead of adding a relationship
    assert result.exit_code == 2
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_mother(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship with a mother"""
    # GIVEN a database with a sample and an case
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    mother = helpers.add_sample(disk_store, sample_id="mother")
    mother_id = mother.internal_id
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-m",
            mother_id,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().mother.internal_id == mother_id


def test_add_relationship_bad_mother(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using a non-existing mother"""
    # GIVEN a database with a sample and an case
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id
    mother_id = "dummy_mother"
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    status = "affected"

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-m",
            mother_id,
        ]
    )

    # THEN then it should not be added
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_father(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using a father"""
    # GIVEN a database with a sample and an case
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    father = helpers.add_sample(disk_store, sample_id="father", gender="male")
    father_id = father.internal_id

    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    status = "affected"

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-f",
            father_id,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().father.internal_id == father_id


def test_add_relationship_bad_father(invoke_cli, disk_store: Store, helpers):
    """Test to add a relationship using a non-existing father"""
    # GIVEN a database with a sample and an case
    sample = helpers.add_sample(disk_store)
    sample_id = sample.internal_id

    father_id = "bad_father"
    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    status = "affected"

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "relationship",
            case_id,
            sample_id,
            "-s",
            status,
            "-f",
            father_id,
        ]
    )

    # THEN then it should not be added
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0
