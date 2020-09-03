import pytest

from cg.meta.workflow.mip import AnalysisAPI
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def mip_lims():
    mip_lims = MockLimsAPI({})
    return mip_lims


@pytest.fixture
def mock_root_folder():
    return "/var/empty"


@pytest.fixture
def mip_context(analysis_store_single_case, tb_api, housekeeper_api, mip_lims, mock_root_folder):
    return {
        "dna_api": AnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=tb_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            deliver_api="deliver",
            script="echo",
            pipeline="analyse rd_dna",
            conda_env="S_mip_rd-dna",
            root=mock_root_folder,
        ),
        "rna_api": AnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=tb_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            deliver_api="deliver",
            script="echo",
            pipeline="analyse rd_rna",
            conda_env="S_mip_rd-rna",
            root=mock_root_folder,
        ),
        "mip-rd-dna": {
            "conda_env": "S_mip_rd-dna",
            "mip_config": "config.yaml",
            "pipeline": "analyse rd_dna",
            "root": mock_root_folder,
            "script": "echo",
        },
        "mip-rd-rna": {
            "conda_env": "S_mip_rd-rna",
            "mip_config": "config.yaml",
            "pipeline": "analyse rd_rna",
            "root": mock_root_folder,
            "script": "echo",
        },
    }
