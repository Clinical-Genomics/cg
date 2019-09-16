"""
    conftest for loqusdb API
"""

import pytest
from cg.apps.gt import GenotypeAPI

CONFIG = {
    'genotype': {
        'database': 'database',
        'binary_path': 'gtdb'
        }
    }

GENOTYPE_TRENDING_OUTPUT = (b'{"ADM1464A1": {"_id": "ADM1464A1", "status": null,' 
                            b'"sample_created_in_genotype_db": "2019-09-02T08:44:55",' 
                            b'"sex": "female", "snps": {}}}')


# genotype fixtures
@pytest.fixture(scope='function')
def genotype_config():
    """
        genotype config fixture
    """

    _config = CONFIG

    return _config


@pytest.fixture(scope='function')
def genotypeapi():
    """
        genotype API fixture
    """

    _genotype_api = GenotypeAPI(CONFIG)
    return _genotype_api


@pytest.fixture(scope='function')
def genotype_trending_output():
    """
        loqusdb stderr for a successful load
    """
    return GENOTYPE_TRENDING_OUTPUT


@pytest.fixture(scope='function')
def loqusdb_case_output():
    """
        loqusdb output for a 'loqusdb cases -c <case_id> --to-json' command
    """

    _output = (b'[{"_id": "1234", "case_id": "a_case", '
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
               b'"_sv_inds": {}}]\n')

    return _output


@pytest.fixture(scope='function')
def loqusdb_duplicate_output():

    """ loqusdb output for a 'loqusdb profile --check-vcf' call"""

    _output = (b'{"ind_id": "proband", "name": "proband", "case_id": "recessive_trio_test", '
               b'"ind_index": 4, "sex": 1, "profile": ["TT", "CC", "CC", "CC", "TT", "AA",'
               b' "CC", "GG", "GG", "GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", "AA", '
               b'"CC", "CC", "CC", "GG", "CC", "CC", "TT", "CC", "AA", "GA", "TC", "AG", "AC", '
               b'"GT", "CC", "AC", "AG", "AG", "AA", "GA", "AA", "CC", "GG", "AA", "TT", "AA", '
               b'"GG", "GG", "CC", "AA", "TT", "TT"]}')

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
