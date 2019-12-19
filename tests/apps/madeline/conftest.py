"""Fixtures for testing the madeline cg app"""

from pathlib import Path

import pytest
from cg.apps.madeline import make_ped


@pytest.fixture
def madeline_columns():
    """return a dictionary with madeline columns"""
    columns = {
        "family": "FamilyId",
        "sample": "IndividualId",
        "sex": "Gender",
        "father": "Father",
        "mother": "Mother",
        "deceased": "Deceased",
        "proband": "Proband",
        "status": "Affected",
    }
    return columns


@pytest.fixture
def proband():
    """return a dictionary with ind info"""
    ind_info = {
        "sample": "proband",
        "sex": "female",
        "father": "father",
        "mother": "mother",
        "deceased": False,
        "proband": True,
        "status": "affected",
    }
    return ind_info


@pytest.fixture
def madeline_input(proband):
    """return a iterable with madeline formated lines"""
    inds = [proband]
    case_id = "test"
    _input = []
    for line in make_ped(case_id, inds):
        _input.append(line)

    return _input


@pytest.fixture
def madeline_process(madeline_output):
    """return a madeline process mock"""
    return MadelineProcessMock(binary="madeline", madeline_file=madeline_output)


class MadelineProcessMock:
    """Class to mock simple madeline process calls"""

    def __init__(
        self, binary, config=None, config_parameter="--config", madeline_file=None
    ):
        """Initialise mock"""
        self.binary = binary
        self.config = config
        self.config_parameter = config_parameter
        self.stdout = ""
        self._madeline_content = ""
        if madeline_file:
            with open(madeline_file, "r") as output:
                self._madeline_content = output.read()

    def run_command(self, parameters):
        """Mock that a command is run"""
        output_prefix = Path(parameters[-2])
        outfile = output_prefix.with_suffix(".xml")
        with open(outfile, "w") as file_handle:
            file_handle.write(self._madeline_content)

        return outfile

    def stdout_lines(self):
        """Iterate over the lines in self.stdout"""
        for line in self.stdout.split("\n"):
            yield line
