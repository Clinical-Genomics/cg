"""Fixtures for cli balsamic tests"""
from collections import namedtuple

import pytest

from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.meta.analysis import AnalysisAPI


@pytest.fixture
def base_context(sample_store):
    """context to use in cli"""
    return {
        'hk_api': MockHouseKeeper(),
        'db': sample_store,
        'analysis_api': MockAnalysis(),
        'fastq_handler': MockBalsamicFastq(),
        'balsamic': {'conda_env': 'conda_env',
                     'root': 'root',
                     'slurm': {'account': 'account', 'qos': 'qos'}
                     }
    }


class MockHouseKeeper(HousekeeperAPI):

    def __init__(self):
        pass

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


class MockAnalysis(AnalysisAPI):

    def __init__(self):
        pass

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


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        pass
