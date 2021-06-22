"""
    Tests for AvatarAPI
"""
import pytest
from cg.apps.avatar.api import Avatar


def test_split_petname():
    """Test to instantiate a avatar api"""
    # GIVEN a merged petname
    merged_petname = "simpleox"

    # WHEN splitting the petname
    split_adjective, split_pet = Avatar._split_petname(merged_petname)

    # THEN the parts of the petname should be the same as the original merged one
    assert split_adjective + split_pet == merged_petname


@pytest.mark.parametrize("adjective", ["apt", "adapted"])
def test_split_petname_ambigous_adjective(adjective):
    """Test to instantiate a avatar api"""
    # GIVEN a merged petname from an ambigous adjective and straightforward pet
    pet = "husky"
    merged_petname = adjective + pet

    # WHEN splitting the petname
    split_petname = Avatar._split_petname(merged_petname)

    # THEN the parts of the petname should be the same as the original merged one
    assert split_petname[0] + split_petname[1] == merged_petname


@pytest.mark.parametrize("pet", ["cat", "cattle", "wildcat"])
def test_split_petname_ambigous_pet(pet):
    """Test to instantiate a avatar api"""
    # GIVEN a merged petname from an ambigous pet and straightforward adjective
    adjective = "strong"
    merged_petname = adjective + pet

    # WHEN splitting the petname
    split_petname = Avatar._split_petname(merged_petname)

    # THEN the parts of the petname should be the same as the original merged one
    assert split_petname[0] + split_petname[1] == merged_petname
