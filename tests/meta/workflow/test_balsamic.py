"""Tests for BALSAMIC analysis"""
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
    try:
        BalsamicAnalysisAPI.get_verified_gender(sample_obj)
    except BalsamicStartError:
        # THEN gender must match the expected one
        assert (
            "Unable to retrieve a valid gender from samples: ['ACC0000A0', 'ACC0000A1']"
            in caplog.text
        )
