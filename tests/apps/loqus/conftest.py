"""
    conftest for loqusdb API
"""

import pytest
from cg.apps.loqus import LoqusdbAPI

CONFIG = {
    'loqusdb': {
        'config': 'loqusdb_config',
        'binary': 'loqusdb'
        }
    }

LOQUSDB_OUTPUT = (b'2018-11-29 08:41:38 130-229-8-20-dhcp.local '
                  b'mongo_adapter.client[77135] INFO Connecting to '
                  b'uri:mongodb://None:None@localhost:27017\n'
                  b'2018-11-29 08:41:38 130-229-8-20-dhcp.local '
                  b'mongo_adapter.client[77135] INFO Connection '
                  b'established\n2018-11-29 08:41:38 130-229-8-20-dhcp.local '
                  b'mongo_adapter.adapter[77135] INFO'
                  b' Use database loqusdb\n2018-11-29 08:41:38 130-229-8-20-dhcp.local '
                  b'loqusdb.utils.vcf[77135]'
                  b' INFO Check if vcf is on correct format...\n'
                  b'2018-11-29 08:41:38 130-229-8-20-dhcp.local'
                  b' loqusdb.utils.vcf[77135] INFO Vcf file '
                  b'/Users/mansmagnusson/Projects/loqusdb/tests/fixtures'
                  b'/test.vcf.gz looks fine\n2018-11-29 '
                  b'08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]'
                  b' INFO Nr of variants in vcf: 15\n2018-11-29 '
                  b'08:41:38 130-229-8-20-dhcp.local loqusdb.utils.'
                  b'vcf[77135] INFO Type of variants in vcf: snv\n'
                  b'Inserting variants\n2018-11-29 08:41:38 130-22'
                  b'9-8-20-dhcp.local loqusdb.utils.load[77135] '
                  b'INFO Inserted 15 variants of type snv\n2018-11-2'
                  b'9 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] '
                  b'INFO Nr variants inserted: '
                  b'15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local '
                  b'loqusdb.commands.load[77135] INFO Time to '
                  b'insert variants: 0:00:00.012648\n2018-11-29 '
                  b'08:41:38 130-229-8-20-dhcp.local loqusdb.plugins.'
                  b'mongo.adapter[77135] INFO All indexes exists\n')

# Loqusdb fixtures
@pytest.fixture(scope='function')
def loqus_config():
    """
        loqusdb config fixture
    """

    _config = CONFIG

    return _config


@pytest.fixture(scope='function')
def loqusdbapi():
    """
        loqusdb API fixture
    """

    _loqus_api = LoqusdbAPI(CONFIG)
    return _loqus_api


@pytest.fixture(scope='function')
def loqusdb_output():
    """
        loqusdb stderr for a successful load
    """
    return LOQUSDB_OUTPUT


@pytest.fixture(scope='function')
def loqusdb_case_output():
    """
        loqusdb output for a 'loqusdb cases -c <case_id> --to-json' command
    """

    _output = (b'[{"_id": "5cc1afbd290c541036a0837f", "case_id": "a_case", '
               b'"vcf_path": "test.vcf.gz", "vcf_sv_path": null, "nr_variants": 15, '
               b'"nr_sv_variants": null, "profile_path": "test.vcf.gz", "individuals": '
               b'[{"ind_id": "proband", "name": "proband", "case_id": "recessive_trio", '
               b'"ind_index": 2, "sex": 1, "profile": ["CC", "TT", "TT", "CC", "TT", '
               b'"AA", "CC", "GG", "GG", "GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", '
               b'"AA", "CC", "CC", "CC", "GG", "CC", "CC", "TT", "CC", "GG", "GG", "TT", '
               b'"AA", "AA", "GG", "CC", "AA", "AA", "AA", "AA", "GG", "GG", "TT", "GG", '
               b'"AA", "TT", "AA", "GG", "GG", "CC", "AA", "TT", "TT"]}, {"ind_id": '
               b'"mother", "name": "mother", "case_id": "recessive_trio", "ind_index": 1, '
               b'"sex": 2, "profile": ["CC", "TT", "TT", "CC", "TT", "AA", "CC", "GG", '
               b'"GG", "GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", "AA", "CC", "CC", '
               b'"CC", "GG", "CC", "CC", "TT", "CC", "GG", "GG", "TT", "AA", "AA", "GG", '
               b'"CC", "AA", "AA", "AA", "AA", "GG", "GG", "TT", "GG", "AA", "TT", "AA", '
               b'"GG", "GG", "CC", "AA", "TT", "TT"]}, {"ind_id": "father", "name": '
               b'"father", "case_id": "recessive_trio", "ind_index": 0, "sex": 1, '
               b'"profile": ["CC", "TT", "TT", "CC", "TT", "AA", "CC", "GG", "GG", '
               b'"GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", "AA", "CC", "CC", '
               b'"CC", "GG", "CC", "CC", "TT", "CC", "GG", "GG", "TT", "AA", "AA", '
               b'"GG", "CC", "AA", "AA", "AA", "AA", "GG", "GG", "TT", "GG", "AA", '
               b'"TT", "AA", "GG", "GG", "CC", "AA", "TT", "TT"]}], "sv_individuals": '
               b'[], "_inds": {"proband": {"ind_id": "proband", "name": "proband", '
               b'"case_id": "recessive_trio", "ind_index": 2, "sex": 1}, "mother": '
               b'{"ind_id": "mother", "name": "mother", "case_id": "recessive_trio", '
               b'"ind_index": 1, "sex": 2}, "father": {"ind_id": "father", "name": '
               b'"father", "case_id": "recessive_trio", "ind_index": 0, "sex": 1}}, '
               b'"_sv_inds": {}}]')

    return _output


@pytest.fixture(scope='function')
def popen_obj_mock():

    """
        Return mocked subprocess.Popen instance
    """

    return PopenMock(mock_stdout=LOQUSDB_OUTPUT.decode('utf-8').split('\n'))


class PopenMock():
    """
        Mock subprocess.Popen class
    """
    def __init__(self, mock_stdout):
        self.mock_stdout = mock_stdout

    @staticmethod
    def poll():
        "mock poll method of Popen"
        return 0

    @property
    def stdout(self):
        "mock stdout of Popen"
        for line in self.mock_stdout:
            yield line.encode()
