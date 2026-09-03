"""Test some of the core functionality of the Housekeeper API."""

from pathlib import Path
from unittest.mock import call, create_autospec

import pytest
from housekeeper.store.models import File, Version
from pytest_mock import MockerFixture
from sqlalchemy.exc import OperationalError

from cg.apps.housekeeper import hk
from cg.apps.housekeeper.hk import HousekeeperAPI


def test_non_initialised_db(hk_config: dict, hk_tag: str):
    """Test to use a database that is not initialised."""
    # GIVEN a housekeeper api and some Housekeeper configs
    api = HousekeeperAPI(hk_config)

    # GIVEN a api without the database
    with pytest.raises(OperationalError):
        # THEN it should raise a operational error
        api.add_tag(hk_tag)


def test_init_db(hk_config: dict, hk_tag: str):
    """Test to setup the database."""
    # GIVEN a Housekeeper API and a Housekeeper config
    api = HousekeeperAPI(hk_config)

    # WHEN initiating the database
    api.initialise_db()

    # THEN the api should not throw an exception
    assert api.add_tag(hk_tag)


def test_finalize_file_transactions_includes_files(
    housekeeper_api: HousekeeperAPI, mocker: MockerFixture
):
    """Test to finalize file transactions and include files."""
    # GIVEN a Housekeeper API, a list of files and a bundle
    commit_spy = mocker.spy(housekeeper_api._store.session, "commit")
    link_spy = mocker.patch.object(hk.os, "link")
    files: list[File] = [
        create_autospec(File, path="path/file1", to_archive=False),
        create_autospec(File, path="path/file2", to_archive=False),
    ]
    version: Version = create_autospec(Version, relative_root_dir="some/path")

    # WHEN finalizing the file transactions
    housekeeper_api.finalize_file_transactions(files=files, version=version)

    # THEN the files should have been linked to the bundle directory
    root_dir = Path(housekeeper_api.get_root_dir())
    expected_calls = [
        call("path/file1", Path(root_dir, "some/path", "file1")),
        call("path/file2", Path(root_dir, "some/path", "file2")),
    ]
    link_spy.assert_has_calls(expected_calls)
    assert link_spy.call_count == 2

    # THEN the commit method should be called once
    commit_spy.assert_called_once()


def test_finalize_file_transactions_empty_file_list(
    housekeeper_api: HousekeeperAPI, mocker: MockerFixture
):
    """Test that finalizing with no files does not link or commit."""
    # GIVEN a Housekeeper API, an empty list of files and a version
    commit_spy = mocker.spy(housekeeper_api._store.session, "commit")
    link_spy = mocker.patch.object(hk.os, "link")
    version: Version = create_autospec(Version, relative_root_dir="some/path")

    # WHEN finalizing file transactions with no files
    housekeeper_api.finalize_file_transactions(files=[], version=version)

    # THEN no linking should happen and no commit should be performed
    link_spy.assert_not_called()
    commit_spy.assert_not_called()
