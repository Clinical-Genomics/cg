from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    raredisease,
    rnafusion,
)


@pytest.fixture
def write_raredisease_mock(mocker: MockerFixture) -> mock.MagicMock:
    """Mock the write_yaml_nextflow_style function."""
    return mocker.patch.object(raredisease, "write_yaml_nextflow_style", return_value=None)


@pytest.fixture
def write_rnafusion_mock(mocker: MockerFixture) -> mock.MagicMock:
    """Mock the write_yaml_nextflow_style function for RNAFusion."""
    return mocker.patch.object(rnafusion, "write_yaml_nextflow_style", return_value=None)
