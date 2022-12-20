"""Test how the api handles files."""
from datetime import datetime
from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from tests.mocks.hk_mock import MockHousekeeperAPI

from housekeeper.store.models import Version, File

from tests.small_helpers import SmallHelpers


def test_new_file(bed_file: Path, housekeeper_api: MockHousekeeperAPI, small_helpers: SmallHelpers):
    """Test to create a new file with the Housekeeper API"""
    # GIVEN a housekeeper api without files and the path to an existing file
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0
    assert bed_file.exists() is True

    # WHEN creating a new file
    new_file = housekeeper_api.new_file(path=bed_file.as_posix())

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == bed_file.as_posix()

    # THEN assert that no file is added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0


def test_new_file_non_existing_path(housekeeper_api: MockHousekeeperAPI):
    """Test to create a new file with the Housekeeper API."""
    # GIVEN a housekeeper api without files and the path to a not existing file
    file_name = Path("a_file.hello")
    assert file_name.exists() is False

    # WHEN creating a new file
    new_file: File = housekeeper_api.new_file(path=file_name.as_posix())

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == file_name.as_posix()


def test_add_new_file(
    populated_housekeeper_api: MockHousekeeperAPI,
    case_id: str,
    madeline_output: Path,
    small_helpers: SmallHelpers,
    not_existing_hk_tag: str,
):
    """Test to create a new file with the Housekeeper API."""
    # GIVEN a populated housekeeper api and the existing version of a bundle
    version: Version = populated_housekeeper_api.last_version(bundle=case_id)

    # GIVEN an existing file that is not included in the database
    assert madeline_output.exists() is True

    # GIVEN a tag that does not exist
    assert populated_housekeeper_api.tag(name=not_existing_hk_tag) is None

    # GIVEN a known number of files in the db
    nr_files_in_db = small_helpers.length_of_iterable(populated_housekeeper_api.files())

    # WHEN creating a new file
    new_file: File = populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version, tags=not_existing_hk_tag
    )

    # THEN assert a file object was created
    assert new_file

    # THEN assert that the path is correct
    assert new_file.path == madeline_output.resolve().as_posix()

    # THEN assert that the file was not added to the database
    new_nr_files = small_helpers.length_of_iterable(populated_housekeeper_api.files())
    assert new_nr_files == nr_files_in_db + 1


def test_get_files(
    populated_housekeeper_api: MockHousekeeperAPI,
    case_id: str,
    tags: List[str],
    small_helpers: SmallHelpers,
):
    """Test get files method."""
    # GIVEN a populated housekeeper api with some files
    nr_files = small_helpers.length_of_iterable(populated_housekeeper_api.files())
    assert nr_files > 0

    # WHEN fetching all files
    files = populated_housekeeper_api.get_files(bundle=case_id, tags=tags)

    # THEN assert all files where fetched
    assert small_helpers.length_of_iterable(files) == nr_files


def test_get_file(populated_housekeeper_api: MockHousekeeperAPI):
    """Test to get a file from the database."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN the id of a file that exists in HK
    assert hk_file

    # WHEN fetching the file with get_file
    hk_file = populated_housekeeper_api.get_file(hk_file.id)

    # THEN assert a file was returned
    assert hk_file is not None


def test_get_file_from_latest_version(case_id: str, populated_housekeeper_api: MockHousekeeperAPI):
    """Test to get a file from the database from the latest version."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN a tag of a file that exists in HK
    assert hk_file.tags

    # WHEN fetching the file with get_file
    hk_file: File = populated_housekeeper_api.get_file_from_latest_version(
        bundle_name=case_id, tags=[hk_file.tags[0].name]
    )

    # THEN assert a file was returned
    assert hk_file is not None


def test_delete_file(populated_housekeeper_api: HousekeeperAPI):
    """Test to delete a file from the database."""
    # GIVEN a housekeeper api with a file
    hk_file: File = populated_housekeeper_api.files().first()

    # GIVEN the id of a file that exists in HK
    assert hk_file

    # WHEN deleting the file
    populated_housekeeper_api.delete_file(hk_file.id)

    # THEN assert the file was removed
    assert populated_housekeeper_api.get_file(hk_file.id) is None


def test_get_included_path(populated_housekeeper_api: MockHousekeeperAPI, case_id: str):
    """Test to get the included path for a file."""
    # GIVEN a populated housekeeper api and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())

    # GIVEN a version and a file object
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]

    # WHEN fetching the included path
    included_path: Path = populated_housekeeper_api.get_included_path(
        root_dir=root_dir, version_obj=version, file_obj=hk_file
    )

    # THEN assert that there is no file existing in the included path
    assert included_path.exists() is False

    # THEN assert that the correct path was created
    assert included_path == Path(root_dir, version.relative_root_dir, Path(hk_file.path).name)


def test_get_include_file(populated_housekeeper_api: MockHousekeeperAPI, case_id: str):
    """Test to get the included path for a file."""
    # GIVEN a populated housekeeper api and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]
    original_path: Path = Path(hk_file.path)
    included_path: Path = Path(root_dir, version.relative_root_dir, original_path.name)

    # GIVEN that the included file does not exist
    assert included_path.exists() is False

    # WHEN including the file
    included_file = populated_housekeeper_api.include_file(hk_file, version)

    # THEN assert that the file has been linked to the included place
    assert included_path.exists() is True

    # THEN assert that the file path has been updated
    assert included_file.path != original_path


def test_include_files_to_latest_version(
    populated_housekeeper_api: MockHousekeeperAPI, case_id: str
):
    """Test to include files for a bundle."""
    # GIVEN a populated Housekeeper API and the root dir
    root_dir: Path = Path(populated_housekeeper_api.get_root_dir())
    version: Version = populated_housekeeper_api.last_version(case_id)
    hk_file: File = version.files[0]
    original_path: Path = Path(hk_file.path)
    included_path: Path = Path(root_dir, version.relative_root_dir, original_path.name)

    # GIVEN that the included file does not exist
    assert included_path.exists() is False

    # WHEN including the file
    populated_housekeeper_api.include_files_to_latest_version(bundle_name=case_id)

    hk_version: Version = populated_housekeeper_api.get_latest_bundle_version(bundle_name=case_id)
    included_file: File = hk_version.files[0]

    # THEN assert that the file has been linked to the included place
    assert included_path.exists() is True

    # THEN assert that the file path has been updated
    assert included_file.path != original_path


def test_check_bundle_files(
    case_id: str,
    timestamp: datetime,
    populated_housekeeper_api: MockHousekeeperAPI,
    hk_version: Version,
    fastq_file: Path,
    sample_id: str,
    bed_file: Path,
):
    """Test to see if the function correctly identifies a file that is present and returns a lis without it."""
    # GIVEN a housekeeper version with a file
    version: Version = populated_housekeeper_api.version(bundle=case_id, date=timestamp)

    # WHEN attempting to add two files, one existing and one new
    files_to_add: List[Path] = populated_housekeeper_api.check_bundle_files(
        file_paths=[bed_file, fastq_file],
        bundle_name=case_id,
        last_version=version,
    )

    # Then only the new file should be returned
    assert files_to_add == [fastq_file]


def test_get_tag_names_from_file(populated_housekeeper_api: MockHousekeeperAPI):
    """Test get tag names on a file."""
    # GIVEN a housekeeper api with a file
    hk_file = populated_housekeeper_api.files().first()
    assert hk_file.tags

    # WHEN fetching tags of a file
    tag_names = populated_housekeeper_api.get_tag_names_from_file(hk_file)

    # THEN a list of tag names is returned
    assert tag_names is not None

    # THEN the return type is a list of strings
    assert isinstance(tag_names, list)
    assert all(isinstance(elem, str) for elem in tag_names)
