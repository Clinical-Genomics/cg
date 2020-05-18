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
