from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.implementations import mip_dna
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


def test_get_config(mock_status_db: Store, mocker: MockerFixture):
    """Test that the MIP DNA configurator can get a case config."""

    # GIVEN an email address in the environment
    mocker.patch.object(mip_dna, "environ_email", return_value="test@scilifelab.se")

    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(store=mock_status_db)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id)

    # THEN case_id, slurm_qos and email should be set
    assert case_config.case_id == "test_case"
    assert case_config.slurm_qos == SlurmQos.NORMAL
    assert case_config.email == "test@scilifelab.se"
    assert case_config.start_after_recipe is None
    assert case_config.start_with_recipe is None


def test_get_config_all_flags_set(mock_status_db: Store):
    """Test that the MIP DNA configurator can get a case config."""

    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(store=mock_status_db)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(
        case_id=case_id,
        start_after_recipe="banana_bread",
        start_with_recipe="short_bread",
        use_bwa_mem=True,
    )

    # THEN we should run the analysis with bwa_mem instead of bwa_mem2
    assert case_config.bwa_mem == 1
    assert case_config.bwa_mem2 == 0
    assert getattr(case_config, "use_bwa_mem", None) is None

    assert case_config.start_after_recipe == "banana_bread"
    assert case_config.start_with_recipe == "short_bread"
