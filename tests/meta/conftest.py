import pytest
from _pytest import tmpdir
from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.apps.usalt.fastq import USaltFastqHandler

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
        'internal_id': 'yellowhog',
        'panels': ['IEM', 'EP'],
        'samples': [{
            'name': 'son',
            'sex': 'male',
            'internal_id': 'ADM1',
            'father': 'ADM2',
            'mother': 'ADM3',
            'status': 'affected',
            'ticket_number': 123456,
            'reads': 5000000,
            'capture_kit': 'GMSmyeloid',
            'data_analysis': 'PIM',
        }, {
            'name': 'father',
            'sex': 'male',
            'internal_id': 'ADM2',
            'status': 'unaffected',
            'ticket_number': 123456,
            'reads': 6000000,
            'capture_kit': 'GMSmyeloid',
            'data_analysis': 'PIM',
        }, {
            'name': 'mother',
            'sex': 'female',
            'internal_id': 'ADM3',
            'status': 'unaffected',
            'ticket_number': 123456,
            'reads': 7000000,
            'capture_kit': 'GMSmyeloid',
            'data_analysis': 'PIM',
        }]
    }
    return family


@pytest.yield_fixture(scope='function')
def analysis_store(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer('cust000')
    family = base_store.Family(name=analysis_family['name'], panels=analysis_family[
        'panels'], internal_id=analysis_family['internal_id'], priority='standard')
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application('WGTPCFC030').versions[0]
    for sample_data in analysis_family['samples']:
        sample = base_store.add_sample(name=sample_data['name'], sex=sample_data['sex'],
                                       internal_id=sample_data['internal_id'],
                                       ticket=sample_data['ticket_number'],
                                       reads=sample_data['reads'],
                                       capture_kit=sample_data['capture_kit'],
                                       data_analysis=sample_data['data_analysis'])
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


class MockFile:

    def __init__(self, path):
        self.path = path

    def first(self):
        return MockFile()

    def full_path(self):
        return ''


class MockDeliver:

    def get_post_analysis_files(self, family: str, version, tags):

        if tags[0] == 'mip-config':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_config.yaml'
        elif tags[0] == 'sampleinfo':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_qc_sample_info.yaml'
        if tags[0] == 'qcmetrics':
            path = '/mnt/hds/proj/bioinfo/bundles/' + family + '/2018-01-30/' + family + \
                   '_qc_metrics.yaml'

        return [MockFile(path=path)]

    def get_post_analysis_files_root_dir(self):
        return ''


class MockPath:

    def __init__(self, path):
        self.yaml = None

    def __call__(self, *args, **kwargs):
        return self

    def open(self):
        return dict()

    def joinpath(self, path):
        return ''


class MockLogger:
    warnings = []

    def warning(self, text: str):
        self.warnings.append(text)

    def get_warnings(self) -> list:
        return self.warnings


class MockTB:
    _get_trending_raises_keyerror = False

    def get_trending(self, mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict) -> dict:
        if self._get_trending_raises_keyerror:
            raise KeyError('mockmessage')

        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'ADM1': 'female', 'ADM2': 'female', 'ADM3': 'female'},
            'family': 'yellowhog',
            'duplicates': {'ADM1': 13.525, 'ADM2': 12.525, 'ADM3': 14.525},
            'genome_build': 'hg19',
            'mapped_reads': {'ADM1': 98.8, 'ADM2': 99.8, 'ADM3': 97.8},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
            'genome_build': '37',
            'rank_model_version': '1.18',
        }

        return outdata

    def get_sampleinfo(self, analysis_obj):
        return ''

    def make_config(self, data):
        return data


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={'balsamic': {'root': tmpdir}})


class MockUsaltFastq(USaltFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={'usalt': {'root': tmpdir}})


def safe_loader(path):
    """Mock function for loading yaml"""

    if path:
        pass

    return {'human_genome_build': {'version': ''}, 'program': {'rankvariant': {'rank_model': {
        'version': 1.18}}}}


@pytest.yield_fixture(scope='function')
def analysis_api(analysis_store, store_housekeeper, scout_store):
    """Setup an analysis API."""
    Path_mock = MockPath('')
    tb_mock = MockTB()

    _analysis_api = AnalysisAPI(
        db=analysis_store,
        hk_api=store_housekeeper,
        scout_api=scout_store,
        tb_api=tb_mock,
        lims_api=None,
        deliver_api=MockDeliver(),
        yaml_loader=safe_loader,
        path_api=Path_mock,
        logger=MockLogger()
    )
    yield _analysis_api
