"""Fixtures for cli balsamic tests"""
import pytest


@pytest.fixture
def base_context():
    """context to use in cli"""
    return {
        'balsamic': {'conda_env': 'conda_env',
                     'root': 'root',
                     'slurm': {'account': 'account', 'qos': 'qos'}
                     }
    }
