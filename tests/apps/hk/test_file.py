"""Test how the api handles files"""
from pathlib import Path


def test_new_file(housekeeper_api, bed_file):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a housekeeper api wihtout files and the path to an existing file
    assert len(list(file_obj for file_obj in housekeeper_api.files())) == 0
    assert Path(bed_file).exists() is True
    # WHEN creating a new file
    new_file_obj = housekeeper_api.new_file(path=bed_file)
    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == bed_file
    # THEN assert that no file is added to the database
    assert len(list(file_obj for file_obj in housekeeper_api.files())) == 0


def test_new_file_non_existing_path(housekeeper_api):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a housekeeper api wihtout files and the path to an existing file
    file_name = "a_file.hello"
    assert Path(file_name).exists() is False
    # WHEN creating a new file
    new_file_obj = housekeeper_api.new_file(path=file_name)
    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == file_name


def test_add_new_file(populated_housekeeper_api, case_id, madeline_output):
    """Test to create a new file with the housekeeper api"""
    # GIVEN a populated housekeeper api and the existing version of a bundle
    version_obj = populated_housekeeper_api.last_version(bundle=case_id)
    # GIVEN an existing file that is not included in the database
    assert Path(madeline_output).exists() is True
    # GIVEN a tag that does not exist
    tag = "madeline"
    assert populated_housekeeper_api.tag(name=tag) is None
    # THEN assert that no file is added to the database
    nr_files_in_db = len(
        list(file_obj for file_obj in populated_housekeeper_api.files())
    )

    # WHEN creating a new file
    new_file_obj = populated_housekeeper_api.add_file(
        path=madeline_output, version_obj=version_obj, tags=tag
    )
    # THEN assert a file object was created
    assert new_file_obj
    # THEN assert that the path is correct
    assert new_file_obj.path == str(Path(madeline_output).resolve())
    # THEN assert that the file was not added to the database
    assert (
        len(list(file_obj for file_obj in populated_housekeeper_api.files()))
        == nr_files_in_db + 1
    )
