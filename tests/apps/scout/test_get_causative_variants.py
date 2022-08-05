"""Tests for the scout api"""

import logging

from cg.apps.scout.scout_export import Variant
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.constants import FileFormat
from cg.io.controller import ReadStream


def test_get_causative_variants_no_variants(scout_api: ScoutAPI, case_id: str):
    """Test to get causative variants when there are no variants"""
    # GIVEN a scout api and a process that returns no std output
    assert scout_api.process.stdout == ""

    # WHEN querying for causative variants
    result = scout_api.get_causative_variants(case_id=case_id)

    # THEN assert that the empty list is returned since there where no variants
    assert result == []


def test_get_causative_variants_one_variant(
    scout_api: ScoutAPI, case_id: str, causative_output: str
):
    """Test to get causative variants when there is one variant"""
    scout_api.process.set_stdout(causative_output)
    # GIVEN a scout api and a process that returns some relevant input
    assert scout_api.process.stdout == causative_output

    # WHEN reading the yaml formatted string
    raw_info: dict = ReadStream.get_content_from_stream(
        file_format=FileFormat.YAML, stream=causative_output
    )

    # WHEN querying for causative variants
    result = scout_api.get_causative_variants(case_id=case_id)

    # THEN assert that the output is a empty list
    assert isinstance(result, list)

    # THEN assert that there was one variant in the list
    assert len(result) == 1
    first_variant: Variant = result[0]

    # THEN assert that the variant has a variant_id
    assert first_variant.document_id == raw_info[0]["_id"]


def test_get_causative_variants_non_existing_case(
    scout_api: ScoutAPI, case_id: str, causative_output: str, caplog
):
    """Test to get causative variants when the case does not exist"""
    caplog.set_level(logging.INFO)
    # GIVEN a scout api and a process that will fail
    scout_api.process.set_exit_code(1)

    # WHEN querying for causative variants
    result = scout_api.get_causative_variants(case_id=case_id)

    # THEN assert that the output is a empty list
    assert isinstance(result, list)
    # THEN assert that the information is communicated
    assert "Could not find case" in caplog.text
