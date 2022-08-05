"""Tests for BALSAMIC analysis"""
from pathlib import Path

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


def test_get_verified_gender_error():
    """Tests gender extraction from a sample dictionary when two different gender has been provided"""

    # GIVEN a sample object with different genders
    sample_obj = {
        "ACC0000A0": {"gender": "male"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_gender(sample_obj)


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


def test_get_verified_pon():
    """Tests PON verification"""

    # GIVEN specific panel bed and PON files
    panel_bed = "/path/gmcksolid_4.1_hg19_design.bed"
    pon_cnn = "/path/PON/gmcksolid_4.1_hg19_design_CNVkit_PON_reference_v2.cnn"
    invalid_pon_cnn = "/path/PON/gmssolid_15.2_hg19_design_CNVkit_PON_reference_v2.cnn"

    # WHEN validating the PON
    validated_pon = BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, pon_cnn)

    # THEN the PON verification should be performed successfully
    assert pon_cnn == validated_pon
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, invalid_pon_cnn)
