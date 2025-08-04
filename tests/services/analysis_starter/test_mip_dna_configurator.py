from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig


def test_get_config_bwa_mem_override():
    """Test that the MIP DNA configurator can get a case config."""
    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator()

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id, use_bwa_mem=True)

    # THEN
    assert case_config.bwa_mem == 1
    assert case_config.bwa_mem2 == 0
