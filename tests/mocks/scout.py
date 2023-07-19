"""Mock the scout api"""

import logging
from pathlib import Path
from pydantic.v1 import BaseModel, validator
from typing import List
from typing_extensions import Literal

from cg.apps.scout.scoutapi import ScoutAPI
from tests.mocks.process_mock import ProcessMock


LOG = logging.getLogger(__name__)


class MockScoutIndividual(BaseModel):
    sample_id: str = "sample_id"
    sex: str = "female"
    analysis_type: Literal[
        "external",
        "mixed",
        "panel",
        "panel-umi",
        "unknown",
        "wes",
        "wgs",
        "wts",
    ] = "wgs"

    @validator("sample_id", "sex", "analysis_type")
    def field_not_none(cls, value):
        if value is None:
            raise ValueError("sample_id, sex and analysis_type can not be None")
        return value


class MockScoutLoadConfig(BaseModel):
    owner: str = "cust000"
    family: str = "family_id"

    @validator("owner", "family")
    def field_not_none(cls, value):
        if value is None:
            raise ValueError("Owner and family can not be None")
        return value

    class Config:
        validate_assignment = True


class MockScoutAPI(ScoutAPI):
    """Mock class for Scout api"""

    def __init__(self, config=None):
        self._config = config or {}
        self._gene_panel = {}
        self._panels = []
        self._causatives = []
        self._cases = []
        self._upload_report_success = True
        self._alignment_file_updated = 0
        self.process = ProcessMock(binary="scout", error=False)

    # Mock specific functions

    def set_report_fail(self):
        """Sets the upload report to fail"""
        self._upload_report_success = False

    def add_mock_case(self, case: dict):
        """Adds a case tp cases"""
        self._cases.append(case)

    def nr_alignment_updates(self) -> int:
        """Return how many time alignment file was updated"""
        return self._alignment_file_updated

    # Overridden functions

    def upload(self, data: dict, force: bool = False):
        """Load analysis of a new case into Scout."""
        LOG.debug("Case loaded successfully to Scout")

    def export_panels(self, panels: List[str], versions=None):
        """Pass through to export of a list of gene panels."""
        return self._panels

    def get_genes(self, panel_id: str, version: str = None) -> list:
        """Fetch panel genes.

        Args:
            panel_id (str): unique id for the panel
            version (str): version of the panel. If 'None' latest version will be returned

        Returns:
            panel genes: panel genes list
        """
        return self._gene_panel.get("genes")

    def get_cases(self, *args, **kwargs):
        """Interact with cases existing in the database."""

        return self._cases

    def get_causative_variants(self, case_id=None, collaborator=None):
        """
        Get causative variants for a case
        """

        return self._causatives

    def get_solved_cases(self, days_ago):
        """
        Get cases solved within chosen timespan

        Args:
            days_ago (int): Maximum days ago a case has been solved

        Return:
            cases (list): list of cases
        """

        return self._cases

    def upload_delivery_report(self, report_path: str, case_id: str, update: bool = False):
        """Load a delivery report into a case in the database

        If the report already exists the function will exit.
        If the user want to load a report that is already in the database
        'update' has to be 'True'

        Args:
            report_path (string):       Path to delivery report
            case_id     (string):       Case identifier
            update      (bool):         If an existing report should be replaced

        Returns:
            updated_case(dict)

        """

        return self._upload_report_success
