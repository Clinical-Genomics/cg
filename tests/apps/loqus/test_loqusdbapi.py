from cg.apps.loqus import LoqusdbAPI

def test_instatiate(loqus_config):
    """Test to get a case via the api"""
    ## GIVEN a loqusdb api with some configs
    
    ## WHEN instantiating a loqusdb api
    loqusdb = LoqusdbAPI(loqus_config)
    
    ## THEN assert that the adapter was properly instantiated
    assert loqusdb.uri == loqus_config['loqusdb']['database']
    assert loqusdb.db_name == loqus_config['loqusdb']['database_name']
    assert loqusdb.loqusdb_binary == loqus_config['loqusdb']['binary']