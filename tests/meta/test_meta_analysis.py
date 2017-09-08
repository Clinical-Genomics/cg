from cg.apps.hk import HousekeeperAPI
from cg.store import Store
from cg.meta.analysis import AnalysisAPI


def test_config(analysis_store: Store, analysis_api: AnalysisAPI):
    # GIVEN a status db with a family
    family_obj = analysis_store.families().first()
    assert family_obj is not None
    # WHEN generating the MIP config for the family
    mip_config = analysis_api.config(family_obj)
    # THEN it should fill in values accordingly
    assert len(mip_config['samples']) == len(family_obj.links)


# def test_link_sample(analysis_store: Store, store_housekeeper: HousekeeperAPI,
#                      analysis_api: AnalysisAPI, tmpdir):
#     # GIVEN a status db with a sample linked to a family
#     sample_obj = analysis_store.sample('ADM1')
#     link_obj = sample_obj.links[0]
#     assert link_obj is not None
