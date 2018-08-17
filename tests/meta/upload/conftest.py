import pytest

from cg.meta.upload.scoutapi import UploadScoutAPI


class MockVersion:
    def id(self):
        return ''


class MockHouseKeeper:

    def files(self, version, tags):
        return MockFile()

    def version(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


class MockMadeline:

    def make_ped(self, name, samples):
        return ''

    def run(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


@pytest.yield_fixture(scope='function')
def upload_scout_api(analysis_store, store_housekeeper, scout_store, trailblazer_api):

    madeline_mock = MockMadeline()
    hk_mock = MockHouseKeeper()
    tb_mock = MockTB()
    ruamel_mock = MockRuamel()
    Path_mock = MockPath('')

    _api = UploadScoutAPI(
        status_api=analysis_store,
        hk_api=hk_mock,
        scout_api=scout_store,
        madeline_exe='',
        madeline=madeline_mock,
        trailblazer_api=tb_mock,
        ruamel=ruamel_mock,
        Path=Path_mock
    )

    yield _api


@pytest.yield_fixture(scope='function')
def analysis(analysis_store):
    _analysis = analysis_store.add_analysis(pipeline='pipeline', version='version')
    _analysis.family = analysis_store.family('yellowhog')
    _analysis.config_path = 'dummy_path'
    yield _analysis
