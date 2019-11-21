"""Fixtures for cli balsamic tests"""

import pytest
import mock

from pathlib import Path
from cg.apps.lims import LimsAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.store import Store
from cg.meta.upload.scoutapi import UploadScoutAPI


@pytest.fixture
def base_context(base_store: Store) -> dict:
    """context to use in cli"""
        
    return {
        'scout_api': MockScoutApi(),
        'scout_upload_api': MockScoutUploadApi(),
        'housekeeper_api': MockHK(),
        'tb_api': MockTB(),
        'status': MockStore()
    }

class MockTB(TrailblazerAPI):
    
    def __init__(self):
        pass
    
    def get_family_root_dir(self, case_id):
        """docstring for get_family_root_dir"""
        return Path('hej')

class MockHK(HousekeeperAPI):
    
    def __init__(self):
        pass

class MockFamily(object):
    
    def __init__(self):
        self.analyses = ['analysis_obj']

class MockStore(Store):
    def __init__(self):
        pass
    
    def family(self, internal_id: str):
        """docstring for family"""
        return MockFamily()

class MockScoutApi(ScoutAPI):
    def __init__(self):
        """docstring for __init__"""
        pass
    
    def upload(self, scout_config, force=False):
        """docstring for upload"""
        pass

class MockScoutUploadApi(UploadScoutAPI):
    def __init__(self):
        """docstring for __init__"""
        self.config = {}
        self.file_exists = False
    
    def generate_config(self, analysis):
        """Mock the generate config"""
        return self.config
    
    def save_config_file(self, scout_config, file_path):
        """docstring for save_config_file"""
        return
    
    def add_scout_config_to_hk(self, file_path, hk_api, case_id):
        """docstring for add_scout_config_to_hk"""
        if self.file_exists:
            raise FileExistsError('Scout config already exists')
        pass


class MockLims(LimsAPI):
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    _project_name = None
    _sample_sex = None

    def update_project(self, lims_id: str, name=None):
        """Mock lims update_project"""
        self._project_name = name

    def get_updated_project_name(self) -> str:
        """Method to test that update project was called with name parameter"""
        return self._project_name

    def update_sample(self, lims_id: str, sex=None, application: str = None,
                      target_reads: int = None, priority=None):
        """Mock lims update_sample"""
        self._sample_sex = sex

    def get_updated_sample_sex(self) -> str:
        """Method to be used to test that update_sample was called with sex parameter"""
        return self._sample_sex
