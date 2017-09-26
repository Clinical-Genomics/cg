import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.analysis import AnalysisAPI


@pytest.yield_fixture(scope='function')
def scout_store():
    """Setup Scout adapter."""
    yield None


@pytest.yield_fixture(scope='function')
def trailblazer_api(tmpdir):
    """Setup Trailblazer api."""
    root_path = tmpdir.mkdir('families')
    _store = TrailblazerAPI({'trailblazer': {'database': 'sqlite://', 'root': str(root_path),
                                             'script': '.', 'mip_config': '.'}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope='function')
def store_housekeeper(tmpdir):
    """Setup Housekeeper store."""
    root_path = tmpdir.mkdir('bundles')
    _store = HousekeeperAPI({'housekeeper': {'database': 'sqlite://', 'root': str(root_path)}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture
def analysis_family():
    """Build an example family."""
    family = {
        'name': 'family',
        'panels': ['IEM', 'EP'],
        'samples': [{
            'name': 'son',
            'sex': 'male',
            'internal_id': 'ADM1',
            'father': 'ADM2',
            'mother': 'ADM3',
            'status': 'affected',
        }, {
            'name': 'father',
            'sex': 'male',
            'internal_id': 'ADM2',
            'status': 'unaffected',
        }, {
            'name': 'mother',
            'sex': 'female',
            'internal_id': 'ADM3',
            'status': 'unaffected',
        }]
    }
    return family


@pytest.yield_fixture(scope='function')
def analysis_store(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer('cust000')
    family = base_store.add_family(name=analysis_family['name'], panels=analysis_family['panels'])
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application('WGTPCFC030').versions[0]
    for sample_data in analysis_family['samples']:
        sample = base_store.add_sample(name=sample_data['name'], sex=sample_data['sex'],
                                       internal_id=sample_data['internal_id'])
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family['samples']:
        sample_obj = base_store.sample(sample_data['internal_id'])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data['status'],
            father=base_store.sample(sample_data['father']) if sample_data.get('father') else None,
            mother=base_store.sample(sample_data['mother']) if sample_data.get('mother') else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


@pytest.yield_fixture(scope='function')
def analysis_api(analysis_store, store_housekeeper, scout_store, trailblazer_api):
    """Setup an analysis API."""
    _analysis_api = AnalysisAPI(
        db=analysis_store,
        hk_api=store_housekeeper,
        scout_api=scout_store,
        tb_api=trailblazer_api,
        lims_api=None,
    )
    yield _analysis_api
