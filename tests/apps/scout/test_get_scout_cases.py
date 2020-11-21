"""Tests for the get cases functionality in ScoutAPI"""

import logging
from cg.apps.scoutapi import ScoutAPI


def test_get_cases_no_case(scout_api: ScoutAPI, case_id: str):
    """Test to get cases based on case_id when there are no matches"""
    # GIVEN a scout api and a process that returns no std output
    assert scout_api.process.stdout == ""

    # WHEN querying for causative variants
    result = scout_api.get_cases(case_id=case_id)

    # THEN assert that the empty list is returned since there where no variants
    assert result == []


def test_get_cases_one_case(scout_api: ScoutAPI, case_id: str, export_cases_output: str):
    """Test to get causative variants when there is one variant"""
    scout_api.process.set_stdout(export_cases_output)
    # GIVEN a scout api and a process that returns some relevant input
    assert scout_api.process.stdout == export_cases_output

    # WHEN querying for causative variants
    result = scout_api.get_cases(case_id=case_id)

    # THEN assert that the output is a empty list
    assert isinstance(result, list)

    # THEN assert that there was one variant in the list
    assert len(result) == 1

    # THEN assert that the variant has a variant_id
    assert "_id" in result[0]
