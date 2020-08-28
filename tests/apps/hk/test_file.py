"""Test how the api handles files"""
from pathlib import Path


def test_new_file(housekeeper_api, bed_file, small_helpers):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a housekeeper api without files and the path to an existing file
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0
    assert Path(bed_file).exists() is True

    # WHEN creating a new file
    new_file_obj = housekeeper_api.new_file(path=bed_file)

    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == bed_file
    # THEN assert that no file is added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.files()) == 0


def test_new_file_non_existing_path(housekeeper_api):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a housekeeper api without files and the path to a not existing file
    file_name = "a_file.hello"
    assert Path(file_name).exists() is False

    # WHEN creating a new file
    new_file_obj = housekeeper_api.new_file(path=file_name)

    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == file_name


def test_add_new_file(populated_housekeeper_api, case_id, madeline_output, small_helpers):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a populated housekeeper api and the existing version of a bundle
    version_obj = populated_housekeeper_api.last_version(bundle=case_id)
    # GIVEN an existing file that is not included in the database
    assert Path(madeline_output).exists() is True
    # GIVEN a tag that does not exist
    tag = "madeline"
    assert populated_housekeeper_api.tag(name=tag) is None
    # GIVEN a known number of files in the db
    nr_files_in_db = small_helpers.length_of_iterable(populated_housekeeper_api.files())

    # WHEN creating a new file
    new_file_obj = populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version_obj, tags=tag
    )

    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == str(Path(madeline_output).resolve())
    # THEN assert that the file was not added to the database
    new_nr_files = small_helpers.length_of_iterable(populated_housekeeper_api.files())
    assert new_nr_files == nr_files_in_db + 1


def test_get_files(populated_housekeeper_api, case_id, tags, small_helpers):
    """Test to fetch files with the get files method"""
    # GIVEN a populated housekeeper api with some files
    nr_files = small_helpers.length_of_iterable(populated_housekeeper_api.files())
    assert nr_files > 0

    # WHEN fetching all files
    files = populated_housekeeper_api.get_files(bundle=case_id, tags=tags)

    # THEN assert all files where fetched
    assert small_helpers.length_of_iterable(files) == nr_files


def test_get_included_path(populated_housekeeper_api, case_id):
    """Test to get the included path for a file"""
    # GIVEN a populated housekeeper api and the root dir
    root_dir = Path(populated_housekeeper_api.get_root_dir())
    # GIVEN a version and a file object
    version_obj = populated_housekeeper_api.last_version(case_id)
    file_obj = version_obj.files[0]

    # WHEN fetching the included path
    included_path = populated_housekeeper_api.get_included_path(
        root_dir=root_dir, version_obj=version_obj, file_obj=file_obj
    )

    # THEN assert that there is no file existing in the included path
    assert included_path.exists() is False
    # THEN assert that the correct path was created
    assert included_path == root_dir / version_obj.relative_root_dir / Path(file_obj.path).name


def test_get_include_file(populated_housekeeper_api, case_id):
    """Test to get the included path for a file"""
    # GIVEN a populated housekeeper api and the root dir
    root_dir = Path(populated_housekeeper_api.get_root_dir())
    version_obj = populated_housekeeper_api.last_version(case_id)
    file_obj = version_obj.files[0]
    original_path = Path(file_obj.path)
    included_path = root_dir / version_obj.relative_root_dir / original_path.name
    # GIVEN that the included file does not exist
    assert included_path.exists() is False

    # WHEN including the file
    included_file = populated_housekeeper_api.include_file(file_obj, version_obj)

    # THEN assert that the file has been linked to the included place
    assert included_path.exists() is True
    # THEN assert that the file path has been updated
    assert included_file.path != original_path
