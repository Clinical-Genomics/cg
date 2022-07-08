"""Tests for BALSAMIC analysis"""
import pytest

from cg.constants.subject import Gender
from cg.exc import BalsamicStartError

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI


def test_get_verified_gender():
    """Tests gender extraction from a sample dictionary"""

    # GIVEN a sample object
    sample_obj = {
        "ACC0000A0": {"gender": "female"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    retrieved_gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

    # THEN gender must match the expected one
    assert retrieved_gender == "female"


def test_get_verified_gender_error(caplog):
    """Tests gender extraction from a sample dictionary when two different gender has been provided"""

    # GIVEN a sample object with different genders
    sample_obj = {
        "ACC0000A0": {"gender": "male"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_gender(sample_obj)
        # THEN the gender extraction should fail
        assert f"Unable to retrieve a valid gender from samples: {sample_obj.keys()}" in caplog.text


def test_get_verified_gender_unknown(caplog):
    """Tests gender extraction from a sample dictionary when the gender is unknown"""

    # GIVEN a sample object with different genders
    sample_obj = {
        "ACC0000A0": {"gender": "unknown"},
        "ACC0000A1": {"gender": "unknown"},
    }

    # WHEN extracting the gender
    retrieved_gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

    # THEN gender must match the expected one
    assert retrieved_gender == Gender.FEMALE
    assert f"The provided gender is unknown, setting {Gender.FEMALE} as the default" in caplog.text
