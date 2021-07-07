"""
    conftest for loqusdb API
"""

import pytest
from cg.apps.loqus import LoqusdbAPI
from cg.models.cg_config import CGConfig, CommonAppConfig
from tests.mocks.process_mock import ProcessMock

LOQUSDB_OUTPUT = (
    b"2018-11-29 08:41:38 130-229-8-20-dhcp.local "
    b"mongo_adapter.client[77135] INFO Connecting to "
    b"uri:mongodb://None:None@localhost:27017\n"
    b"2018-11-29 08:41:38 130-229-8-20-dhcp.local "
    b"mongo_adapter.client[77135] INFO Connection "
    b"established\n2018-11-29 08:41:38 130-229-8-20-dhcp.local "
    b"mongo_adapter.adapter[77135] INFO"
    b" Use database loqusdb\n2018-11-29 08:41:38 130-229-8-20-dhcp.local "
    b"loqusdb.utils.vcf[77135]"
    b" INFO Check if vcf is on correct format...\n"
    b"2018-11-29 08:41:38 130-229-8-20-dhcp.local"
    b" loqusdb.utils.vcf[77135] INFO Vcf file "
    b"/Users/mansmagnusson/Projects/loqusdb/tests/fixtures"
    b"/test.vcf.gz looks fine\n2018-11-29 "
    b"08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]"
    b" INFO Nr of variants in vcf: 15\n2018-11-29 "
    b"08:41:38 130-229-8-20-dhcp.local loqusdb.utils."
    b"vcf[77135] INFO Type of variants in vcf: snv\n"
    b"Inserting variants\n2018-11-29 08:41:38 130-22"
    b"9-8-20-dhcp.local loqusdb.utils.load[77135] "
    b"INFO Inserted 15 variants of type snv\n2018-11-2"
    b"9 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] "
    b"INFO Nr variants inserted: "
    b"15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local "
    b"loqusdb.commands.load[77135] INFO Time to "
    b"insert variants: 0:00:00.012648\n2018-11-29 "
    b"08:41:38 130-229-8-20-dhcp.local loqusdb.plugins."
    b"mongo.adapter[77135] INFO All indexes exists\n"
)


# Loqusdb fixtures
@pytest.fixture(name="loqus_config")
def fixture_loqus_config():
    """
    loqusdb config fixture
    """
    return {
        "loqusdb": {"config_path": "loqusdb_config_wes", "binary_path": "loqus_binary"},
        "loqusdb_wes": {
            "config_path": "loqusdb_config_wes",
            "binary_path": "loqusdb_wes_binary",
        },
    }


@pytest.fixture(name="loqus_config_object")
def fixture_loqus_config_object(loqus_config: dict, cg_config_object: CGConfig):
    cg_config_object.loqusdb = CommonAppConfig(**loqus_config["loqusdb"])
    cg_config_object.loqusdb_wes = CommonAppConfig(**loqus_config["loqusdb-wes"])
    return cg_config_object


@pytest.fixture(scope="function")
def loqus_binary_path(loqus_config):
    """
    loqusdb binary fixture
    """

    return loqus_config["loqusdb"]["binary_path"]


@pytest.fixture(scope="function")
def loqus_config_path(loqus_config):
    """
    loqusdb binary fixture
    """

    return loqus_config["loqusdb"]["config_path"]


@pytest.fixture(scope="function")
def loqus_process(loqus_binary_path: str, loqus_config_path: str):
    """
    Return mocked cg.utils.Process instance
    """

    return ProcessMock(binary=loqus_binary_path, config=loqus_config_path)


@pytest.fixture(scope="function")
def loqus_process_exception(loqus_binary_path, loqus_config_path):
    """
    Return mocked cg.utils.Process instance
    """

    return ProcessMock(binary=loqus_binary_path, config=loqus_config_path, error=True)


@pytest.fixture(scope="function")
def loqusdbapi(loqus_config: dict, loqus_process):
    """
    loqusdb API fixture
    """

    _loqus_api = LoqusdbAPI(loqus_config)
    _loqus_api.process = loqus_process

    return _loqus_api


@pytest.fixture(scope="function")
def loqusdbapi_exception(loqus_config, loqus_process_exception):
    """
    loqusdb API fixture
    """

    _loqus_api = LoqusdbAPI(loqus_config)
    _loqus_api.process = loqus_process_exception

    return _loqus_api


@pytest.fixture(scope="function")
def loqusdb_output():
    """
    loqusdb stderr for a successful load
    """
    return LOQUSDB_OUTPUT


@pytest.fixture(scope="function")
def loqusdb_case_output():
    """
    loqusdb output for a 'loqusdb cases -c <case_id> --to-json' command
    """

    _output = (
        b'[{"_id": "1234", "case_id": "yellowhog", '
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
        b'"_sv_inds": {}}]\n'
    )

    return _output


@pytest.fixture(scope="function")
def loqusdb_duplicate_output():
    """loqusdb output for a 'loqusdb profile --check-vcf' call"""

    _output = (
        b'{"ind_id": "proband", "name": "proband", "case_id": "recessive_trio_test", '
        b'"ind_index": 4, "sex": 1, "profile": ["TT", "CC", "CC", "CC", "TT", "AA",'
        b' "CC", "GG", "GG", "GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", "AA", '
        b'"CC", "CC", "CC", "GG", "CC", "CC", "TT", "CC", "AA", "GA", "TC", "AG", "AC", '
        b'"GT", "CC", "AC", "AG", "AG", "AA", "GA", "AA", "CC", "GG", "AA", "TT", "AA", '
        b'"GG", "GG", "CC", "AA", "TT", "TT"]}'
    )

    return _output
