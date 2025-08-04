from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def mock_status_db() -> Store:
    mock_store: Store = create_autospec(Store)
    mock_case: Case = create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    mock_store.get_case_by_internal_id = Mock(return_value=mock_case)
    return mock_store


def test_get_config(mock_status_db: Store):
    """Test that the MIP DNA configurator can get a case config."""
    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(store=mock_status_db)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id)

    # THEN
    assert case_config.case_id == "test_case"
    assert case_config.slurm_qos == SlurmQos.NORMAL


def test_get_config_bwa_mem_override(mock_status_db: Store):
    """Test that the MIP DNA configurator can get a case config."""
    # GIVEN a MIP DNA configurator

    configurator = MIPDNAConfigurator(store=mock_status_db)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id, use_bwa_mem=True)

    # THEN
    assert case_config.bwa_mem == 1
    assert case_config.bwa_mem2 == 0
    assert getattr(case_config, "use_bwa_mem", None) is None
