"""
    Tests for loqusdbAPI
"""

import subprocess
import pytest

from cg.apps.loqus import LoqusdbAPI
from cg.apps.loqus import execute_command

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


def test_get_case(loqusdbapi, loqusdb_case_output, mocker):

    """Test to get a case via the api"""
    # GIVEN a loqusdb api
    case_id = 'a_case'
    # WHEN fetching a case with the adapter
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = loqusdb_case_output
    case_obj = loqusdbapi.get_case(case_id)
    # THEN assert that the correct case id is returned
    assert case_obj['case_id'] == case_id


def test_get_case_non_existing(loqusdbapi, mocker):

    """Test to get a case via the api"""

    # GIVEN a loqusdb api and a case id
    case_id = 'a_case'

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
    vcf_sv_path = 'a sv_vcf path'
    gbcf_path = 'a bcf path'

    # WHEN uploading a case with 15 variants to loqusdb
    mocker.patch('cg.apps.loqus.execute_command',
                 return_value=loqusdb_output.decode('utf-8').split('\n'))

    data = loqusdbapi.load(family_id, ped_path, vcf_path, vcf_sv_path, gbcf_path)

    # THEN assert that the number of variants is 15

    assert data['variants'] == 15


def test_repr_string(loqus_config):

    """Test __repr__ of loqusdbAPI"""

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


def test_execute_command(mocker, loqusdb_output, popen_obj_mock):

    """
        Test execute_command function
    """

    # Mock the Popen class
    popen_mock = mocker.patch('subprocess.Popen')
    popen_mock.return_value = popen_obj_mock
    command_output = [line for line in execute_command(['_loqus_', '_command_'])]

    assert command_output == loqusdb_output.decode('utf-8').split('\n')
