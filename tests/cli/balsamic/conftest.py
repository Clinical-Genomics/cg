"""Fixtures for cli balsamic tests"""
from collections import namedtuple

import pytest
from _pytest import tmpdir

from cg.apps.balsamic.fastq import BalsamicFastqHandler


@pytest.fixture
def base_context():
    """context to use in cli"""
    return {
        'hk_api': MockHouseKeeper,
        'db': MockStore,
        'analysis_api': MockAnalysis,
        'fastq_handler': MockBalsamicFastq,
        'balsamic': {'conda_env': 'conda_env',
                     'root': 'root',
                     'slurm': {'account': 'account', 'qos': 'qos'}
                     }
    }


class MockHouseKeeper:

    def files(self, version, tags):
        return MockFile()

    def version(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


class MockVersion:
    def id(self):
        return ''


class MockFile:

    def __init__(self, path=''):
        self.path = path

    def first(self):
        return MockFile()

    def full_path(self):
        return ''


class MockAnalysis:

    def get_latest_metadata(self, family_id):
        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'ADM1': 'female', 'ADM2': 'female', 'ADM3': 'female'},
            'family': 'yellowhog',
            'duplicates': {'ADM1': 13.525, 'ADM2': 12.525, 'ADM3': 14.525},
            'genome_build': 'hg19',
            'rank_model_version': '1.18',
            'mapped_reads': {'ADM1': 98.8, 'ADM2': 99.8, 'ADM3': 97.8},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
        }

        return outdata

    def convert_panels(self, customer_id, panels):
        return ''


class MockStore:
    """We need to call the family function from the store
    without accessing the database. So here we go"""

    def __init__(self):
        """Constructor"""
        self._case_obj = None
        self._case_id = None
        self._family_was_called = False

    def family(self, case_id: str):
        """Mock the family call"""

        case_obj = namedtuple('Case', 'internal_id')
        case_obj.internal_id = 'fake case'
        self._case_id = case_id
        self._case_obj = case_obj

        self._family_was_called = True

        return case_obj

    def family_was_called(self):
        """Check if family was called"""
        return self._family_was_called


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={'balsamic': {'root': tmpdir}})
