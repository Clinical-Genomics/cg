from pathlib import Path

import pytest

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator


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
    "configurator_fixture, case_id_fixture, case_path_fixture",
    [("raredisease_configurator", "raredisease_case_id", "raredisease_case_path")],
    ids=["raredisease"],
)
def test_create_nextflow_config_file_exists(
    configurator_fixture: str,
    case_id_fixture: str,
    case_path_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that a Nextflow config file is created for all Nextflow pipelines."""
    # GIVEN a configurator, a case id and a case path
    configurator: NextflowConfigurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # GIVEN that a case directory exists
    configurator._create_case_directory(case_id=case_id)

    # WHEN creating nextflow config
    configurator.config_file_creator.create(case_id=case_id, case_path=case_path)

    # THEN the nextflow config is created
    case_path: Path = configurator._get_case_path(case_id=case_id)
    assert configurator.config_file_creator.get_file_path(
        case_id=case_id, case_path=case_path
    ).exists()
