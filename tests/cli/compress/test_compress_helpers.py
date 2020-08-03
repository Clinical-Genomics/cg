"""Tests for helper functions in cg compress cli"""

import os
from pathlib import Path

from cg.cli.compress import helpers


def test_get_true_dir_no_symlinks(project_dir):
    """Test to get a true dir when there are no symlinks"""
    # GIVEN a directory with some files but no symlinked files
    a_file = project_dir / "hello.txt"
    a_file.touch()
    assert a_file.exists()
    # WHEN fetching the true dir for the files in fixture dir
    true_dir = helpers.get_true_dir(a_file.parent)
    # THEN assert that the true_dir is None since there where no symbolic links in the project_dir
    assert true_dir is None


def test_get_true_dir_when_symlinks(project_dir):
    """Test to get a true dir when there are symlinks to another directory

    The function should return the path to another directory when there are symlinks in one
    """
    # GIVEN a directory with a file with some content
    content = "hello world"
    a_file = project_dir / "hello.txt"
    a_file.write_text(content)
    assert a_file.exists()
    # GIVEN a subdirectory with a link to the above file
    new_dir = project_dir / "new_dir/"
    new_dir.mkdir()
    a_link = new_dir / "link_to_hello"
    a_link.symlink_to(a_file)
    assert a_link.read_text() == content
    assert a_link.parent == new_dir
    assert a_link.is_symlink() is True

    # WHEN fetching the true dir for the symlinked dir
    true_dir = helpers.get_true_dir(a_link.parent)

    # THEN assert that the true_dir the same as the parent of the destination of the symlink
    assert true_dir == project_dir


def test_get_versions_no_bundle(housekeeper_api):
    """Test to get latest versions of bundles when no bundles exists"""
    # GIVEN a empty housekeeper_api

    # WHEN fetching versions
    versions = helpers.get_versions(housekeeper_api)

    # THEN assert no versions was returned
    assert sum(1 for version in versions) == 0


def test_get_versions_one_bundle(housekeeper_api, spring_bundle):
    """Test to get latest versions of bundles when no bundles exists"""
    # GIVEN a populated housekeeper_api
    housekeeper_api.add_bundle(spring_bundle)

    # WHEN fetching versions
    versions = helpers.get_versions(housekeeper_api)

    # THEN assert no versions was returned
    assert sum(1 for version in versions) == 1


def test_correct_spring_paths(
    housekeeper_api, spring_bundle_symlink_problem, symlinked_fastqs, new_dir
):
    """docstring for test_correct_spring_paths"""
    # GIVEN a populated housekeeper_api
    housekeeper_api.add_bundle(spring_bundle_symlink_problem)
    # GIVEN that the spring files exists in the wrong location
    versions = helpers.get_versions(housekeeper_api)
    version = next(versions)
    for file_path in version.files:
        assert not Path(file_path.full_path).exists()

    # WHEN updating the spring paths
    helpers.correct_spring_paths(housekeeper_api)

    # THEN assert that the spring paths has been moved
    for file_path in version.files:
        assert Path(file_path.full_path).exists()
