"""Tests the Housekeeper API"""

from datetime import datetime


def test_re_include_included_file(tmpdir, hk_api):
    """ tests that file that is included can be re-included """

    # GIVEN an included file
    tag = add_tag(hk_api)
    first_file = create_file(tmpdir, 'first_file')
    second_file = create_file(tmpdir, 'second_file')
    bundle = add_bundle(hk_api)
    version = add_version(hk_api, bundle)
    added_file = hk_api.add_file(first_file, version, tag.name)
    hk_api.include_file(added_file, version)
    first_file_path = get_file_path(added_file)

    # WHEN calling re_include_file()
    hk_api.re_include_file(second_file, added_file, version)

    # THEN the file is still included but with the new path
    second_file_path = get_file_path(added_file)
    assert second_file_path != first_file_path


def test_include_added_file(tmpdir, hk_api):
    """ tests that file that is added can be included """

    # GIVEN a file and an bundle with the file in it
    tag = add_tag(hk_api)
    file = create_file(tmpdir)
    bundle = add_bundle(hk_api)
    version = add_version(hk_api, bundle)
    added_file = hk_api.add_file(file, version, tag.name)
    assert not is_file_included(added_file)

    # WHEN calling include_file()
    hk_api.include_file(added_file, version)

    # THEN the file is included
    assert is_file_included(added_file)


def test_add_file(tmpdir, hk_api):
    """ tests that file that is not already in hk is added """

    # GIVEN a file and an bundle without the file in it
    tag = add_tag(hk_api)
    file = create_file(tmpdir)
    bundle = add_bundle(hk_api)
    version = add_version(hk_api, bundle)
    assert not is_file_in_bundle(hk_api, file, bundle)

    # WHEN calling add_file()
    hk_api.add_file(file, version, tag.name)

    # THEN the file was added to the bundle
    assert is_file_in_bundle(hk_api, file, bundle)


def get_file_path(file):
    """Returns the path to the housekeeper file"""
    return file.path


def is_file_included(file):
    """Returns True if the file is included False otherwise"""

    return file.is_included


def add_tag(hk_api, tag_name='test_tag'):
    """Adds a tag model object for use in tests"""

    new_tag = hk_api.new_tag(tag_name)
    hk_api.add_commit(new_tag)
    return new_tag


def create_file(tmpdir, file_name='test_name', file_content='test_content'):
    """Creates a file on disk to use in tests"""

    file_name = file_name
    file_path = tmpdir / file_name
    file_path.write(file_content)
    return file_path


def add_bundle(hk_api, bundle_name='test_bundle'):
    """Adds a bundle model object for use in tests"""

    new_bundle = hk_api.new_bundle(bundle_name)
    hk_api.add_commit(new_bundle)
    return new_bundle


def add_version(hk_api, bundle):
    """Adds a version model object if for use in tests"""

    new_version = hk_api.new_version(datetime.now())
    new_version.bundle = bundle
    hk_api.add_commit(new_version)
    return new_version


def is_file_in_bundle(hk_api, file_path, bundle):
    """Returns True if the file_path is found in the bundle False otherwise"""

    files = hk_api.get_files(bundle.name, tags=None).all()

    for file in files:
        if file_path == file.path:
            return True

    return False
