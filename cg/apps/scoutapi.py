"""Code for talking to Scout regarding uploads"""

import datetime as dt
import logging
from typing import List
from pathlib import Path

from pymongo import MongoClient
from scout.adapter.mongo import MongoAdapter
from scout.export.panel import export_panels as scout_export_panels
from scout.load import load_scout
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

    def upload(self, data: dict, threshold: int = 5, force: bool = False):
        """Load analysis of a new family into Scout."""
        data["rank_score_threshold"] = threshold
        config_data = parse_case_data(config=data)
        existing_case = self.case(
            institute_id=config_data["owner"], display_name=config_data["family_name"]
        )
        if existing_case:
            if force or config_data["analysis_date"] > existing_case["analysis_date"]:
                LOG.info("update existing Scout case")
                load_scout(self, config_data, update=True)
            else:
                existing_date = existing_case["analysis_date"].date()
                LOG.warning("analysis of case already loaded: %s", existing_date)
            return
        LOG.debug("load new Scout case")
        load_scout(self, config_data)
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
        return scout_export_panels(self, panels, versions)

    def get_genes(self, panel_id: str, version: str = None) -> list:
        """Fetch panel genes.

        Args:
            panel_id (str): unique id for the panel
            version (str): version of the panel. If 'None' latest version will be returned

        Returns:
            panel genes: panel genes list
        """
        gene_panel = self.gene_panel(panel_id=panel_id, version=version)
        return gene_panel.get("genes")

    def get_cases(
        self,
        case_id=None,
        institute=None,
        reruns=None,
        finished=None,
        causatives=None,
        research_requested=None,
        is_research=None,
        status=None,
    ):
        """Interact with cases existing in the database."""

        models = []
        if case_id:
            case_obj = self.case(case_id=case_id)
            if case_obj:
                models.append(case_obj)

        else:
            models = self.cases(
                collaborator=institute,
                reruns=reruns,
                finished=finished,
                has_causatives=causatives,
                research_requested=research_requested,
                is_research=is_research,
                status=status,
            )

        return models

    def get_causative_variants(self, case_id=None, collaborator=None):
        """
        Get causative variants for a case
        """
        causative_ids = self.get_causatives(institute_id=collaborator, case_id=case_id)

        causatives = [self.variant(causative_id) for causative_id in causative_ids]

        return causatives

    def get_solved_cases(self, days_ago):
        """
        Get cases solved within chosen timespan

        Args:
            days_ago (int): Maximum days ago a case has been solved

        Return:
            cases (list): list of cases
        """

        days_datetime = dt.datetime.now() - dt.timedelta(days=days_ago)

        # Look up 'mark_causative' events added since specified number days ago
        event_query = {
            "category": "case",
            "verb": "mark_causative",
            "created_at": {"$gte": days_datetime},
        }
        recent_events = self.event_collection.find(event_query)
        solved_cases = set()

        # Find what cases these events concern
        for event in recent_events:
            solved_cases.add(event["case"])

        solved_cases = list(solved_cases)

        # Find these cases in the database
        cases = self.case_collection.find({"_id": {"$in": solved_cases}})

        return cases

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

        return load_delivery_report(
            adapter=self, case_id=case_id, report_path=report_path, update=update
        )
