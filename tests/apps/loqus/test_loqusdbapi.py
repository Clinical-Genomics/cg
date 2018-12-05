import subprocess

from cg.apps.loqus import LoqusdbAPI

def test_instatiate(loqus_config):
    """Test to instantiate a loqusdb api"""
    ## GIVEN a loqusdb api with some configs

    ## WHEN instantiating a loqusdb api
    loqusdb = LoqusdbAPI(loqus_config)

    ## THEN assert that the adapter was properly instantiated
    assert loqusdb.uri == loqus_config['loqusdb']['database']
    assert loqusdb.db_name == loqus_config['loqusdb']['database_name']
    assert loqusdb.loqusdb_binary == loqus_config['loqusdb']['binary']

def test_get_case(loqusdbapi, mocker):
    """Test to get a case via the api"""
    ## GIVEN a loqusdb api
    case_id = 'a_case'
    ## WHEN fetching a case with the adapter
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = b'[{"_id": "a_case"}]'
    case_obj = loqusdbapi.get_case(case_id)
    ## THEN assert that the correct case id is returned
    assert case_obj['_id'] == case_id

def test_get_case_non_existing(loqusdbapi, mocker):
    """Test to get a case via the api"""
    ## GIVEN a loqusdb api
    case_id = 'a_case'
    ## WHEN fetching a case with the adapter
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.side_effect = subprocess.CalledProcessError(1,'error')
    case_obj = loqusdbapi.get_case(case_id)

    ## THEN assert None is returned
    assert case_obj == None

def test_load(loqusdbapi, mocker, loqusdb_output):
    """Test to load a case"""
    ## GIVEN a loqusdb api and some info about a case
    family_id = 'test'
    ped_path = 'a ped path'
    vcf_path = 'a vcf path'

    ## WHEN loading the case to loqus with the api
    mocker.patch.object(subprocess, 'check_output')
    subprocess.check_output.return_value = loqusdb_output

    data = loqusdbapi.load(family_id, ped_path, vcf_path)

    ## THEN assert that the number of variants is 15

    assert data['variants'] == 15

