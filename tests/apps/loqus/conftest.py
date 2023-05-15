""" Conftest for Loqusdb API."""
from typing import Dict

import pytest
from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LoqusdbInstance
from cg.models.cg_config import CGConfig, CommonAppConfig
from tests.mocks.process_mock import ProcessMock
from tests.models.observations.conftest import (
    fixture_observations_input_files_raw,
    fixture_observations_input_files,
)

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
    b"/Users/username/Projects/loqusdb/tests/fixtures"
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

LOQUSDB_CASE_OUTPUT = (
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

LOQUSDB_DUPLICATE_OUTPUT = (
    b'{"ind_id": "proband", "name": "proband", "case_id": "recessive_trio_test", '
    b'"ind_index": 4, "sex": 1, "profile": ["TT", "CC", "CC", "CC", "TT", "AA",'
    b' "CC", "GG", "GG", "GG", "TT", "GG", "CC", "AA", "GG", "GG", "GG", "AA", '
    b'"CC", "CC", "CC", "GG", "CC", "CC", "TT", "CC", "AA", "GA", "TC", "AG", "AC", '
    b'"GT", "CC", "AC", "AG", "AG", "AA", "GA", "AA", "CC", "GG", "AA", "TT", "AA", '
    b'"GG", "GG", "CC", "AA", "TT", "TT"]}'
)

LOQUSDB_DELETE_STDERR = b"""2022-09-22 12:30:07 username loqusdb.commands.cli[20689] INFO Running loqusdb version 2.6.9
2022-09-22 12:30:07 username mongo_adapter.client[20689] INFO Connecting to uri:mongodb://None:None@localhost:27017
2022-09-22 12:30:07 username mongo_adapter.client[20689] INFO Connection established
2022-09-22 12:30:07 username mongo_adapter.adapter[20689] INFO Use database loqusdb
2022-09-22 12:30:07 username loqusdb.plugins.mongo.case[20689] INFO Removing case yellowhog from database
2022-09-22 12:30:07 username loqusdb.utils.delete[20689] INFO deleting variants
2022-09-22 12:30:07 username loqusdb.utils.delete[20689] INFO Start deleting chromosome 1"""

LOQUSDB_DELETE_NONEXISTING_STDERR = b"""2022-09-22 11:40:04 username loqusdb.commands.cli[19944] INFO Running loqusdb version 2.6.9
2022-09-22 11:40:04 username mongo_adapter.client[19944] INFO Connecting to uri:mongodb://None:None@localhost:27017
2022-09-22 11:40:04 username mongo_adapter.client[19944] INFO Connection established
2022-09-22 11:40:04 username mongo_adapter.adapter[19944] INFO Use database loqusdb
2022-09-22 11:40:04 username loqusdb.commands.delete[19944] WARNING Case yellowhog does not exist in database"""


@pytest.fixture(name="loqusdb_config_dict")
def fixture_loqusdb_config() -> Dict[LoqusdbInstance, dict]:
    """Return Loqusdb config dictionary."""
    return {
        LoqusdbInstance.WGS: {"binary_path": "binary", "config_path": "config"},
        LoqusdbInstance.WES: {"binary_path": "binary_wes", "config_path": "config_wes"},
        LoqusdbInstance.SOMATIC: {"binary_path": "binary_somatic", "config_path": "config_somatic"},
        LoqusdbInstance.TUMOR: {"binary_path": "binary_tumor", "config_path": "config_tumor"},
    }


@pytest.fixture(name="cg_config_locusdb")
def fixture_cg_config_locusdb(
    loqusdb_config_dict: Dict[LoqusdbInstance, dict], cg_config_object: CGConfig
) -> CGConfig:
    """Return CG config for Loqusdb."""
    cg_config_object.loqusdb = CommonAppConfig(**loqusdb_config_dict[LoqusdbInstance.WGS])
    cg_config_object.loqusdb_wes = CommonAppConfig(**loqusdb_config_dict[LoqusdbInstance.WES])
    cg_config_object.loqusdb_somatic = CommonAppConfig(
        **loqusdb_config_dict[LoqusdbInstance.SOMATIC]
    )
    cg_config_object.loqusdb_tumor = CommonAppConfig(**loqusdb_config_dict[LoqusdbInstance.TUMOR])
    return cg_config_object


@pytest.fixture(name="loqusdb_binary_path")
def fixture_loqusdb_binary_path(loqusdb_config_dict: Dict[LoqusdbInstance, dict]) -> str:
    """Return Loqusdb binary path."""
    return loqusdb_config_dict[LoqusdbInstance.WGS]["binary_path"]


@pytest.fixture(name="loqusdb_config_path")
def fixture_loqusdb_config_path(loqusdb_config_dict: Dict[LoqusdbInstance, dict]) -> str:
    """Return Loqusdb config dictionary."""
    return loqusdb_config_dict[LoqusdbInstance.WGS]["config_path"]


@pytest.fixture(name="loqusdb_process")
def fixture_loqusdb_process(loqusdb_binary_path: str, loqusdb_config_path: str) -> ProcessMock:
    """Return mocked process instance."""
    return ProcessMock(binary=loqusdb_binary_path, config=loqusdb_config_path)


@pytest.fixture(name="loqusdb_process_exception")
def fixture_loqusdb_process_exception(
    loqusdb_binary_path: str, loqusdb_config_path: str
) -> ProcessMock:
    """Return error process instance."""
    return ProcessMock(binary=loqusdb_binary_path, config=loqusdb_config_path, error=True)


@pytest.fixture(name="loqusdb_api")
def fixture_loqusdb_api(
    loqusdb_binary_path: str, loqusdb_config_path: str, loqusdb_process: ProcessMock
) -> LoqusdbAPI:
    """Return Loqusdb API."""
    loqusdb_api = LoqusdbAPI(binary_path=loqusdb_binary_path, config_path=loqusdb_config_path)
    loqusdb_api.process = loqusdb_process
    return loqusdb_api


@pytest.fixture(name="loqusdb_api_exception")
def fixture_loqusdb_api_exception(
    loqusdb_binary_path: str, loqusdb_config_path: str, loqusdb_process_exception: ProcessMock
) -> LoqusdbAPI:
    """Return Loqusdb API with mocked error process."""
    loqusdb_api = LoqusdbAPI(binary_path=loqusdb_binary_path, config_path=loqusdb_config_path)
    loqusdb_api.process = loqusdb_process_exception
    return loqusdb_api


@pytest.fixture(name="loqusdb_load_stderr")
def fixture_loqusdb_load_stderr() -> bytes:
    """Return Loqusdb stderr for a successful load."""
    return LOQUSDB_OUTPUT


@pytest.fixture(name="loqusdb_case_output")
def fixture_loqusdb_case_output() -> bytes:
    """Return Loqusdb output for a 'loqusdb cases -c <case_id> --to-json' command."""
    return LOQUSDB_CASE_OUTPUT


@pytest.fixture(name="loqusdb_duplicate_output")
def fixture_loqusdb_duplicate_output() -> bytes:
    """Return Loqusdb output for a 'loqusdb profile --check-vcf' command."""
    return LOQUSDB_DUPLICATE_OUTPUT


@pytest.fixture(name="loqusdb_delete_stderr")
def fixture_loqusdb_delete_stderr() -> bytes:
    """Return Loqusdb STDERR for a successful delete."""
    return LOQUSDB_DELETE_STDERR


@pytest.fixture(name="loqusdb_delete_non_existing_stderr")
def fixture_loqusdb_delete_non_existing_stderr() -> bytes:
    """Return Loqusdb delete STDERR for non existing case."""
    return LOQUSDB_DELETE_NONEXISTING_STDERR


@pytest.fixture(name="nr_of_loaded_variants")
def fixture_nr_of_loaded_variants() -> int:
    """Return number of loaded variants."""
    return 15
