from pathlib import Path
from unittest import mock

import pytest

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.implementations.raredisease import (
    RarediseaseConfigurator,
)


@pytest.mark.parametrize(
    "configurator_fixture, case_config_fixture, case_id_fixture",
    [("raredisease_configurator", "raredisease_case_config", "raredisease_case_id")],
    ids=["raredisease"],
)
def test_create_config(
    configurator_fixture: str,
    case_config_fixture: str,
    case_id_fixture: str,
    raredisease_params_file_path: str,
    raredisease_work_dir_path: str,
    request: pytest.FixtureRequest,
):
    """Test creating the case config for all pipelines."""
    # GIVEN a configurator and a case id
    configurator: Configurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # WHEN creating a case config
    case_config: CaseConfig = configurator.create_config(case_id=case_id)

    # THEN the expected case config is returned
    expected_case_config: CaseConfig = request.getfixturevalue(case_config_fixture)
    assert case_config == expected_case_config


@pytest.mark.parametrize(
    "configurator_fixture, case_id_fixture",
    [("raredisease_configurator", "raredisease_case_id")],
    ids=["raredisease"],
)
def test_create_nextflow_config_file_exists(
    configurator_fixture: str,
    case_id_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that a nextflow config file is created fro all Nextflow pipelines."""
    # GIVEN a configurator and a case id
    configurator: RarediseaseConfigurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # GIVEN that a case directory exists
    configurator._create_case_directory(case_id=case_id, dry_run=False)

    # WHEN creating nextflow config
    configurator._create_nextflow_config(case_id=case_id, dry_run=False)

    # THEN the nextflow config is created
    assert configurator._get_nextflow_config_path(case_id).exists()


@pytest.mark.parametrize(
    "configurator_fixture, case_id_fixture, expected_content_fixture",
    [("raredisease_configurator", "raredisease_case_id", "expected_raredisease_config_content")],
    ids=["raredisease"],
)
def test_get_nextflow_config_content(
    configurator_fixture: str,
    case_id_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that the content of the nextflow config file is accurate for all Nextflow pipelines."""
    # GIVEN a configurator and a case id
    configurator: RarediseaseConfigurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # WHEN getting nextflow config content
    nextflow_config_content: str = configurator._get_nextflow_config_content(case_id=case_id)

    # THEN the expected content is returned
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert nextflow_config_content.rstrip() == expected_content.rstrip()
