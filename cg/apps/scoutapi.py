"""Code for talking to Scout regarding uploads"""

import datetime as dt
import logging
from typing import List, Optional
from pathlib import Path
import yaml
import json

from subprocess import CalledProcessError


from pymongo import MongoClient
from scout.adapter.mongo import MongoAdapter
from scout.export.panel import export_panels as scout_export_panels
from scout.load.report import load_delivery_report
from scout.parse.case import parse_case_data
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class ScoutAPI(MongoAdapter):

    """Interface to Scout."""

    def __init__(self, config):
        client = MongoClient(config["scout"]["database"], serverSelectionTimeoutMS=20)
        super(ScoutAPI, self).__init__(client[config["scout"]["database_name"]])

        binary_path = config["scout"]["binary_path"]
        config_path = config["scout"]["config_path"]
        self.process = Process(binary=binary_path, config=config_path)

    def upload(self, scout_load_config: Path, threshold: int = 5, force: bool = False):
        """Load analysis of a new family into Scout."""
        with open(scout_load_config, "r") as stream:
            data = yaml.safe_load(stream)
        config_data = parse_case_data(config=data)
        existing_case = self.case(
            institute_id=config_data["owner"], display_name=config_data["family_name"]
        )
        load_command = ["load", "case", str(scout_load_config)]
        if existing_case:
            if force or config_data["analysis_date"] > existing_case["analysis_date"]:
                load_command.append("--update")
                LOG.info("update existing Scout case")
            else:
                existing_date = existing_case["analysis_date"].date()
                LOG.warning("analysis of case already loaded: %s", existing_date)
                return
        LOG.debug("load new Scout case")
        self.process.run_command(load_command)
        LOG.debug("Case loaded successfully to Scout")

    def update_alignment_file(self, case_id: str, sample_id: str, alignment_path: Path):
        """Update alignment file for individual in case"""
        parameters = [
            "update",
            "individual",
            "--case-id",
            case_id,
            "--ind-id",
            sample_id,
            "--alignment-path",
            str(alignment_path),
        ]
        self.process.run_command(parameters=parameters)

    def export_panels(self, panels: List[str], versions=None):
        """Pass through to export of a list of gene panels."""
        # This can be run from CLI with `scout export panels --bed <panen1> <panel2>`
        return scout_export_panels(self, panels, versions)

    def get_genes(self, panel_id: str, version: str = None) -> list:
        """Fetch panel genes.

        Args:
            panel_id (str): unique id for the panel
            version (str): version of the panel. If 'None' latest version will be returned

        Returns:
            panel genes: panel genes list
        """
        # This can be run from CLI with `scout export panels <panel1> `
        gene_panel = self.gene_panel(panel_id=panel_id, version=version)
        return gene_panel.get("genes")

    def get_cases(
        self,
        case_id: Optional[str] = None,
        reruns: bool = False,
        finished: bool = False,
        status: Optional[str] = None,
    ) -> List[dict]:
        """Interact with cases existing in the database."""
        # These commands can be run with `scout export cases`
        get_cases_command = ["export", "cases", "--json"]
        if case_id:
            get_cases_command.extend(["--case-id", case_id])

        elif status:
            get_cases_command.extend(["--status", status])

        elif finished:
            get_cases_command.extend(["--finished"])

        if reruns:
            LOG.info("Fetching cases that are reruns")
            get_cases_command.append("--reruns")

        try:
            self.process.run_command(get_cases_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find cases")
            return []

        return json.loads(self.process.stdout)

    def get_causative_variants(self, case_id: str) -> List[dict]:
        """
        Get causative variants for a case
        """
        # These commands can be run with `scout export variants`
        get_causatives_command = ["export", "variants", "case-id", case_id]
        try:
            self.process.run_command(get_causatives_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.warning("Could not find case %s in scout", case_id)
            return []

        return json.loads(self.process.stdout)

    def get_solved_cases(self, days_ago: int):
        """
        Get cases solved within chosen timespan

        Args:
            days_ago (int): Maximum days ago a case has been solved

        Return:
            cases (list): list of cases
        """
        solved_cases_command = [
            "export",
            "cases",
            "--json",
            "--status",
            "--solved",
            "--within-days",
            str(days_ago),
        ]
        try:
            self.process.run_command(solved_cases_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.warning("Could not find any solved cases in scout")
            return []

        return json.loads(self.process.stdout)

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
        # This command can be run with `scout load delivery-report <CASE-ID> <REPORT-PATH>`

        return load_delivery_report(
            adapter=self, case_id=case_id, report_path=report_path, update=update
        )
