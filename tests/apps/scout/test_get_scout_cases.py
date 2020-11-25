"""Tests for the get cases functionality in ScoutAPI"""

from datetime import datetime
from cg.apps.scout.scoutapi import ScoutAPI


def test_get_cases_no_case(scout_api: ScoutAPI, case_id: str):
    """Test to get cases based on case_id when there are no matches"""
    # GIVEN a scout api and a process that returns no std output
    assert scout_api.process.stdout == ""

    # WHEN querying for cases
    result = scout_api.get_cases(case_id=case_id)

    # THEN assert that the empty list is returned since there where cases in scout
    assert result == []


def test_get_cases_one_case(scout_api: ScoutAPI, case_id: str, export_cases_output: str):
    """Test to get get a case based on case_id when there is a case in scout"""
    scout_api.process.set_stdout(export_cases_output)
    # GIVEN a scout api and a process that returns some relevant input
    assert scout_api.process.stdout == export_cases_output

    # WHEN querying for cases
    result = scout_api.get_cases(case_id=case_id)

    # THEN assert that the output is a list
    assert isinstance(result, list)
    # THEN assert that there was one case in the list
    assert len(result) == 1
    case_data = result[0]

    # THEN assert that the case has a _id
    assert case_data.id
    # THEN assert that the analysis date is a datetime object
    assert isinstance(case_data.analysis_date, datetime)
