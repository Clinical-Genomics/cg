import pytest
from cg.apps.loqus import LoqusdbAPI


## Loqusdb fixtures
@pytest.fixture(scope='function')
def loqus_config():
    _config = {
        'loqusdb': {
            'database': 'mongodb://localhost',
            'database_name': 'loqusdb',
            'binary': 'loqusdb',
        }
    }
    
    return _config

@pytest.fixture(scope='function')
def loqusdbapi(loqus_config):
    _loqus_api = LoqusdbAPI(loqus_config)
    return _loqus_api