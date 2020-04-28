"""Tests for madeline extension"""

from cg.apps.madeline.api import MadelineAPI
from cg.utils import Process


def get_ind_info(columns, line):
    """Take some madeline columns and a raw madeline line and create a dictionary"""
    ind_info = dict(zip(columns, line.rstrip().split("\t")))
    return ind_info


def test_run_madeline(mocker, trio, madeline_output):
    """Test to run the madeline call from api"""
    # GIVEN a ped stream and a madeline process mock
    config = {"madeline_exe": "madeline"}
    madeline_api = MadelineAPI(config)
    mocker.patch.object(Process, "run_command")
    # WHEN running the madeline command
    outpath = madeline_api.run("a family", trio, madeline_output)
    # THEN assert a madeline xml file is returned
    assert outpath.endswith(".xml")


def test_generate_madeline_input_no_mother(madeline_columns, proband):
    """Test generate input for madeline when mother is missing"""
    # GIVEN a family id and a ind with unknown mother
    family_id = "test"
    proband.pop("mother")
    inds = [proband]
    # WHEN generating madeline formated lines
    madeline_lines = MadelineAPI.make_ped(family_id, inds)
    i = 0
    for i, line in enumerate(madeline_lines, 1):
        if i == 1:
            continue
        ind_info = get_ind_info(madeline_columns.keys(), line)

    # THEN assert that the mother is set to '.', meaning no mother exists
    assert ind_info["mother"] == "."


def test_generate_madeline_input_no_sex(madeline_columns, proband):
    """Test generate input for madeline when sex is missing"""

    # GIVEN a family id and a ind with unknown sex
    family_id = "test"
    proband["sex"] = "unknown"
    inds = [proband]
    # WHEN generating madeline formated lines
    madeline_lines = MadelineAPI.make_ped(family_id, inds)
    i = 0
    for i, line in enumerate(madeline_lines, 1):
        if i == 1:
            continue
        ind_info = get_ind_info(madeline_columns.keys(), line)

    # THEN assert that sex is set to '.', meaning sex is unknown
    assert ind_info["sex"] == "."


def test_generate_madeline_input(madeline_columns, proband):
    """Test generate input for madeline"""

    # GIVEN a family id and a list of ind dicts
    family_id = "test"
    inds = [proband]
    # WHEN generating madeline formated lines
    madeline_lines = MadelineAPI.make_ped(family_id, inds)
    # Skip the header line
    next(madeline_lines)
    # Convert line to dict
    ind_info = get_ind_info(madeline_columns.keys(), next(madeline_lines))

    # THEN assert that the family id is included
    assert ind_info["family"] == family_id
    # THEN assert that the ind id information is correct
    assert ind_info["sample"] == proband["sample"]
    # THEN assert that the is converted to madeline format
    assert ind_info["sex"] == "F"


def test_generate_madeline_input_none_status(madeline_columns, proband):
    """Test generate input for madeline"""

    # GIVEN a family id and a list of ind dicts
    proband["status"] = None
    family_id = "test"
    inds = [proband]
    # WHEN generating madeline formated lines
    madeline_lines = MadelineAPI.make_ped(family_id, inds)
    # Skip the header line
    next(madeline_lines)
    # Convert line to dict
    ind_info = get_ind_info(madeline_columns.keys(), next(madeline_lines))

    # THEN assert that the status is "."
    assert ind_info["status"] == "."


def test_generate_madeline_input_non_existing_status(madeline_columns, proband):
    """Test generate input for madeline"""

    # GIVEN an individual without status
    proband.pop("status")
    assert "status" not in proband
    family_id = "test"
    # GIVEN a family id and a list of ind dicts
    inds = [proband]
    # WHEN generating madeline formated lines
    madeline_lines = MadelineAPI.make_ped(family_id, inds)
    # Skip the header line
    next(madeline_lines)
    # Convert line to dict
    ind_info = get_ind_info(madeline_columns.keys(), next(madeline_lines))

    # THEN assert that the status is "."
    assert ind_info["status"] == "."


def test_generate_madeline_input_no_inds(madeline_columns):
    """Test generate input for madeline when no individuals"""

    # GIVEN a family id and a empty list of inds
    family_id = "test"
    inds = []
    # WHEN generating madeline formated lines
    res = MadelineAPI.make_ped(family_id, inds)
    # THEN assert that only the header line was generated
    i = 0
    header_line = None
    for i, line in enumerate(res, 1):
        header_line = line
    assert header_line == "\t".join(madeline_columns.values())
    # THEN assert only the header line is returned
    assert i == 1
