"""
    Tests for VogueAPI
"""

from cg.apps.vogue import VogueAPI


def test_instatiate(vogue_config):

    """Test to instantiate a vogue api"""

    # GIVEN a vogue api with a config

    # WHEN instantiating a vogue api
    vogue_api = VogueAPI(vogue_config)

    # THEN assert that the adapter was properly instantiated
    assert vogue_api.vogue_binary == vogue_config['vogue']['binary_path']
