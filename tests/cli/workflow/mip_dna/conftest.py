
import pytest

from cg.meta.workflow.mip import AnalysisAPI

class MockLimsAPI:
    """Mock LIMS API to simulate LIMS behavior in BALSAMIC"""

    def __init__(self, config: dict = None):
        self.config = config
        self.sample_vars = {}

    def add_sample(self, internal_id: str):
        self.sample_vars[internal_id] = {}

    def add_capture_kit(self, internal_id: str, capture_kit):
        if not internal_id in self.sample_vars:
            self.add_sample(internal_id)
        self.sample_vars[internal_id]["capture_kit"] = capture_kit

    def capture_kit(self, internal_id: str):
        if internal_id in self.sample_vars:
            return self.sample_vars[internal_id].get("capture_kit")
        return None


@pytest.fixture
def mip_lims():
    mip_lims = MockLimsAPI({})
    return mip_lims

@pytest.fixture
def mip_context(analysis_store_single_case, tb_api, housekeeper_api, mip_lims):
    return {
    "db": analysis_store_single_case,
    "tb": tb_api,
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
        root="/tmp"),
        
    "mip-rd-dna": {
        "conda_env": "S_mip_rd-dna",
        "mip_config": "config.yaml",
        "pipeline": "analyse rd_dna",
        "root": "/tmp",
        "script": "echo",
        },
    "mip-rd-rna": {
        "conda_env": "S_mip_rd-rna",
        "mip_config": "config.yaml",
        "pipeline": "analyse rd_rna",
        "root": "/tmp",
        "script": "echo",
        }
    }