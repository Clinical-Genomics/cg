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


def test_get_latest_data(analysis_api: AnalysisAPI):

    # GIVEN
    family_id = 'dummy_family_id'

    # WHEN
    trending_data = analysis_api.get_latest_data('dummy_family_id')

    # THEN
    assert trending_data['genome_build']
    assert trending_data['rank_model_version']


def test_get_latest_trending_data(analysis_api: AnalysisAPI):
    # GIVEN an initialised report_api and the deliver_api does not have what we want
    analysis_api.tb._get_trending_raises_keyerror = True

    # WHEN failing to get latest trending data for a family
    latest_data = analysis_api.get_latest_data(family_id='bluebull')

    # THEN there should be a log entry about this
    assert 'bluebull' in analysis_api.LOG.get_last_warning()
    assert not latest_data
