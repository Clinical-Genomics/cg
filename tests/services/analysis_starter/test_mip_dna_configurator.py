from unittest.mock import Mock, create_autospec

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.models import Case
from cg.store.store import Store


def test_get_config():
    """Test that the MIP DNA configurator can get a case config."""
    # GIVEN a MIP DNA configurator
    mock_store: Store = create_autospec(Store)
    mock_case: Case = create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    mock_store.get_case_by_internal_id = Mock(return_value=mock_case)

    configurator = MIPDNAConfigurator(store=mock_store)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id)

    # THEN
    assert case_config.case_id == "test_case"
    assert case_config.slurm_qos == SlurmQos.NORMAL


def test_get_config_bwa_mem_override():
    """Test that the MIP DNA configurator can get a case config."""
    # GIVEN a MIP DNA configurator
    mock_store: Store = create_autospec(Store)
    configurator = MIPDNAConfigurator(store=mock_store)

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id, use_bwa_mem=True)

    # THEN
    assert case_config.bwa_mem == 1
    assert case_config.bwa_mem2 == 0
    assert getattr(case_config, "use_bwa_mem", None) is None
