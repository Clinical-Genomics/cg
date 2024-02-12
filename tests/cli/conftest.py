"""Fixtures for CLI tests."""

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.cli.compress.conftest import CaseInfo
from tests.store_helpers import StoreHelpers


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CliRunner"""
    return CliRunner()


@pytest.fixture
def application_tag() -> str:
    """Return a dummy tag"""
    return "dummy_tag"


@pytest.fixture
def base_context(
    base_store: Store, housekeeper_api: HousekeeperAPI, cg_config_object: CGConfig
) -> CGConfig:
    """context to use in CLI."""
    cg_config_object.status_db_ = base_store
    cg_config_object.housekeeper_api_ = housekeeper_api
    return cg_config_object


@pytest.fixture
def before_date() -> str:
    """Return a before date string"""
    return "1999-12-31"


@pytest.fixture
def disk_store(base_context: CGConfig) -> Store:
    """context to use in cli"""
    return base_context.status_db


class MockCompressAPI(CompressAPI):
    """Mock out necessary functions for running the compress CLI functions."""

    def __init__(self):
        """initialize mock"""
        super().__init__(hk_api=None, crunchy_api=None, demux_root="")
        self.ntasks = 12
        self.mem = 50
        self.fastq_compression_success = True
        self.spring_decompression_success = True
        self.dry_run = False

    def set_dry_run(self, dry_run: bool):
        """Update dry run."""
        self.dry_run = dry_run

    def compress_fastq(self, sample_id: str, dry_run: bool = False):
        """Return if compression was successful."""
        _ = sample_id, dry_run
        return self.fastq_compression_success

    def decompress_spring(self, sample_id: str, dry_run: bool = False):
        """Return if decompression was succesful."""
        _ = sample_id, dry_run
        return self.spring_decompression_success


@pytest.fixture
def compress_api():
    """Return a compress API context."""
    return MockCompressAPI()


@pytest.fixture
def compress_context(
    compress_api: CompressAPI, store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context."""
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = store
    return cg_config_object


@pytest.fixture
def compress_case_info(
    case_id,
    family_name,
    timestamp,
    later_timestamp,
    wgs_application_tag,
):
    """Returns a object with information about a case."""
    return CaseInfo(
        case_id=case_id,
        family_name=family_name,
        timestamp=timestamp,
        later_timestamp=later_timestamp,
        application_tag=wgs_application_tag,
    )


@pytest.fixture
def populated_compress_store(store, helpers, compress_case_info, analysis_family):
    """Return a store populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    helpers.ensure_case_from_dict(
        store,
        case_info=analysis_family,
        app_tag=compress_case_info.application_tag,
        ordered_at=compress_case_info.timestamp,
        completed_at=compress_case_info.later_timestamp,
    )
    return store


@pytest.fixture
def populated_compress_context(
    compress_api: CompressAPI, populated_compress_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


@pytest.fixture
def real_crunchy_api(crunchy_config: dict[str, dict[str, Any]]):
    """Return Crunchy API."""
    _api = CrunchyAPI(crunchy_config)
    _api.set_dry_run(True)
    yield _api


@pytest.fixture
def real_compress_api(
    illumina_demultiplexed_runs_directory,
    housekeeper_api: HousekeeperAPI,
    real_crunchy_api: CrunchyAPI,
) -> CompressAPI:
    """Return a compress API context."""
    return CompressAPI(
        crunchy_api=real_crunchy_api,
        hk_api=housekeeper_api,
        demux_root=illumina_demultiplexed_runs_directory.as_posix(),
    )


@pytest.fixture
def real_populated_compress_fastq_api(
    real_compress_api: CompressAPI, compress_hk_fastq_bundle: dict, helpers: StoreHelpers
) -> CompressAPI:
    """Return real populated compress API."""
    helpers.ensure_hk_bundle(real_compress_api.hk_api, compress_hk_fastq_bundle)

    return real_compress_api


@pytest.fixture
def real_populated_compress_context(
    real_populated_compress_fastq_api: CompressAPI,
    populated_compress_store: Store,
    cg_config_object: CGConfig,
) -> CGConfig:
    """Return a compress context populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = real_populated_compress_fastq_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


@pytest.fixture
def scout_export_manged_variants_output() -> str:
    return """##fileformat=VCFv4.2
##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the variant described in this record">
##fileDate=2023-12-07 16:35:38.814086
##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Type of structural variant">
##INFO=<ID=TYPE,Number=1,Type=String,Description="Type of variant">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	48696925	.	G	C	.		END=48696925;TYPE=SNV
14	76548781	.	CTGGACC	G	.		END=76548781;TYPE=INDEL"""


@pytest.fixture
def scout_panel_output() -> str:
    return """##genome_build=37
##gene_panel=OMIM-AUTO,version=22.0,updated_at=2023-10-17,display_name=OMIM-AUTO
##gene_panel=PANELAPP-GREEN,version=6.0,updated_at=2023-10-19,display_name=PanelApp Green Genes
##contig=1
##contig=2
##contig=3
##contig=4
##contig=5
##contig=6
##contig=7
##contig=8
##contig=9
##contig=10
##contig=X
##contig=Y
##contig=MT
#chromosome	gene_start	gene_stop	hgnc_id	hgnc_symbol
1	568915	569121	44571	MTATP8P1
1	860260	879955	28706	SAMD11
2       162164549       162268228       16889   PSMD14
2       162272605       162282381       11590   TBR1
3       120315156       120321347       7699    NDUFB4
3       120347020       120401418       4892    HGD
4       185570767       185616117       26575   PRIMPOL
4       185676749       185747972       3569    ACSL1
5       473425  524447  11073   SLC9A3
5       892758  919472  12307   TRIP13
6       18224099        18265054        2768    DEK
6       19837617        19840915        5363    ID4
7       44256749        44374176        1461    CAMK2B
7       44646171        44748665        8124    OGDH
8       22993101        23021543        11907   TNFRSF10D
8       23047965        23082639        11904   TNFRSF10A
9       35099888        35103154        14559   STOML2
9       35161999        35405335        12566   UNC13B
10      23481256        23483181        23734   PTF1A
10      25305587        25315593        26160   THNSL1
X       154719776       154899605       18308   TMLHE
X       155110956       155173433       11486   VAMP7
Y       6778727 6959724 18502   TBL1Y
Y       14813160        14972764        12633   USP9Y
MT      577     647     7481    MT-TF
MT      648     1601    7470    MT-RNR1"""
