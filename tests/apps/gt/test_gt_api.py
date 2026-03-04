"""
Tests for GenotypeAPI
"""

from cg.apps.gt import GenotypeAPI


def test_instantiate(genotype_config: dict):
    """Test to instantiate a genotype api"""
    # GIVEN a genotype api with a config

    # WHEN instantiating a genotype api
    genotype_api = GenotypeAPI(genotype_config)

    # THEN assert that the adapter was properly instantiated
    assert genotype_api.process.config == genotype_config["genotype"]["config_path"]
    assert genotype_api.process.binary == genotype_config["genotype"]["binary_path"]
