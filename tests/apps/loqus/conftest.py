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

@pytest.fixture(scope='function')
def loqusdb_output():
    _loqus_output = (b'2018-11-29 08:41:38 130-229-8-20-dhcp.local '
    b'mongo_adapter.client[77135] INFO Connecting to uri:mongodb://None:None@localhost:27017\n'
    b'2018-11-29 08:41:38 130-229-8-20-dhcp.local mongo_adapter.client[77135] INFO Connection '
    b'established\n2018-11-29 08:41:38 130-229-8-20-dhcp.local mongo_adapter.adapter[77135] INFO'
    b' Use database loqusdb\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]'
    b' INFO Check if vcf is on correct format...\n2018-11-29 08:41:38 130-229-8-20-dhcp.local'
    b' loqusdb.utils.vcf[77135] INFO Vcf file /Users/mansmagnusson/Projects/loqusdb/tests/fixtures'
    b'/test.vcf.gz looks fine\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]'
    b' INFO Nr of variants in vcf: 15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.'
    b'vcf[77135] INFO Type of variants in vcf: snv\nInserting variants\n2018-11-29 08:41:38 130-22'
    b'9-8-20-dhcp.local loqusdb.utils.load[77135] INFO Inserted 15 variants of type snv\n2018-11-2'
    b'9 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] INFO Nr variants inserted: '
    b'15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] INFO Time to '
    b'insert variants: 0:00:00.012648\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.plugins.'
    b'mongo.adapter[77135] INFO All indexes exists\n')
    return _loqus_output


