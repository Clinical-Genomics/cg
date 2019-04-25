"""
    Tests for loqusdbAPI
"""

import subprocess
import pytest

from cg.apps.loqus import LoqusdbAPI

from cg.exc import CaseNotFoundError


def test_instatiate(loqus_config):

    """Test to instantiate a loqusdb api"""
    # GIVEN a loqusdb api with some configs

    # WHEN instantiating a loqusdb api
    loqusdb = LoqusdbAPI(loqus_config)

    # THEN assert that the adapter was properly instantiated
    assert loqusdb.db_name == loqus_config['loqusdb']['database_name']
    assert loqusdb.loqusdb_binary == loqus_config['loqusdb']['binary']
    assert loqusdb.host == loqus_config['loqusdb']['host']
    assert loqusdb.port == loqus_config['loqusdb']['port']
    assert loqusdb.password == loqus_config['loqusdb']['password']
    assert loqusdb.username == loqus_config['loqusdb']['username']


def test_get_case(loqusdbapi, mocker):

    """Test to get a case via the api"""
    # GIVEN a loqusdb api
    case_id = 'a_case'
    # WHEN fetching a case with the adapter
    mocker.patch.object(subprocess, 'check_output')
    loqusdb_output = (b"{'_id': 'one_case', 'case_id': 'one_case'}\n"
                      b"{'_id': 'a_case', 'case_id': 'a_case'}\n")
    subprocess.check_output.return_value = loqusdb_output
    case_obj = loqusdbapi.get_case(case_id)
    # THEN assert that the correct case id is returned
    assert case_obj['_id'] == case_id


def test_get_case_non_existing(loqusdbapi, mocker):

    """Test to get a case via the api"""

    # GIVEN a loqusdb api and a case id
    case_id = 'a_case'

    # WHEN case is not in the loqusdb output
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = b"{'_id': 'case', 'case_id': 'case'}\n"

    # THEN CaseNotFoundError should be raised
    with pytest.raises(CaseNotFoundError):
        loqusdbapi.get_case(case_id)

    # WHEN loqusdb output is empty string
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = b""

    # THEN CaseNotFoundError should be raised
    with pytest.raises(CaseNotFoundError):
        loqusdbapi.get_case(case_id)


def test_get_case_command_fail(loqusdbapi, mocker):

    """Test to see if exception is raised"""
    # GIVEN a loqusdb api and a case id
    case_id = 'a_case'
    # WHEN an error occurs during fetching a case with the adapter
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.side_effect = subprocess.CalledProcessError(1, 'error')

    # THEN assert that the error is raised
    with pytest.raises(subprocess.CalledProcessError):
        loqusdbapi.get_case(case_id)


def test_load(loqusdbapi, mocker, loqusdb_output):

    """Test to load a case"""
    # GIVEN a loqusdb api and some info about a case
    family_id = 'test'
    ped_path = 'a ped path'
    vcf_path = 'a vcf path'

    # WHEN uploading a case with 15 variants to loqusdb
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = loqusdb_output

    data = loqusdbapi.load(family_id, ped_path, vcf_path)

    # THEN assert that the number of variants is 15

    assert data['variants'] == 15


def test_repr_string(loqus_config):

    loqusdb = LoqusdbAPI(loqus_config)

    repr_string = repr(loqusdb)

    uri = (f"mongodb://{loqus_config['loqusdb']['username']}:"
           f"{loqus_config['loqusdb']['password']}@"
           f"{loqus_config['loqusdb']['host']}:"
           f"{loqus_config['loqusdb']['port']}/"
           f"{loqus_config['loqusdb']['database_name']}")

    correct_string = (f"LoqusdbAPI(uri={uri},"
                      f"db_name={loqus_config['loqusdb']['database_name']},"
                      f"loqusdb_binary={loqus_config['loqusdb']['binary']})")

    assert repr_string == correct_string
