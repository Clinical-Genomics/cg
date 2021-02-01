"""Code for talking to Scout regarding uploads"""

import json
import logging
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Optional

import yaml

from cg.apps.scout.scout_export import ScoutExportCase, Variant
from cg.meta.upload.scout.scout_load_config import ScoutLoadConfig
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class ScoutAPI:

    """Interface to Scout."""

    def __init__(self, config):

        binary_path = config["scout"]["binary_path"]
        config_path = config["scout"]["config_path"]
        self.process = Process(binary=binary_path, config=config_path)

    def upload(self, scout_load_config: Path, threshold: int = 5, force: bool = False):
        """Load analysis of a new family into Scout."""
        with open(scout_load_config, "r") as stream:
            data = yaml.safe_load(stream)
        scout_load_config_object: ScoutLoadConfig = ScoutLoadConfig(**data)
        existing_case: Optional[ScoutExportCase] = self.get_case(
            case_id=scout_load_config_object.family
        )
        load_command = ["load", "case", str(scout_load_config)]
        if existing_case:
            if force or scout_load_config_object.analysis_date > existing_case.analysis_date:
                load_command.append("--update")
                LOG.info("update existing Scout case")
            else:
                existing_date = existing_case.analysis_date.date()
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

    def export_panels(self, panels: List[str], build: str = None) -> List[str]:
        """Pass through to export of a list of gene panels.

        Return list of lines in bed format
        """
        export_panels_command = ["export", "panel", "--bed"]
        for panel_id in panels:
            export_panels_command.append(panel_id)

        if build:
            export_panels_command.extend(["--build", build])

        try:
            self.process.run_command(export_panels_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find panels")
            return []

        return [line for line in self.process.stdout_lines()]

    def get_genes(self, panel_id: str, build: str = None) -> list:
        """Fetch panel genes.

        Args:
            panel_id (str): unique id for the panel
            version (str): version of the panel. If 'None' latest version will be returned

        Returns:
            panel genes: panel genes list
        """
        # This can be run from CLI with `scout export panels <panel1> `
        export_panel_command = ["export", "panel", panel_id]
        if build:
            export_panel_command.extend(["--build", build])

        try:
            self.process.run_command(export_panel_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find panel %s", panel_id)
            return []

        panel_genes = []
        for gene_line in self.process.stdout_lines():
            if gene_line.startswith("#"):
                continue
            gene_info = gene_line.strip().split("\t")
            if not len(gene_info) > 1:
                continue
            panel_genes.append({"hgnc_id": int(gene_info[0]), "hgnc_symbol": gene_info[1]})

        return panel_genes

    def get_causative_variants(self, case_id: str) -> List[Variant]:
        """
        Get causative variants for a case
        """
        # These commands can be run with `scout export variants`
        get_causatives_command = ["export", "variants", "--json", "--case-id", case_id]
        try:
            self.process.run_command(get_causatives_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.warning("Could not find case %s in scout", case_id)
            return []
        variants: List[Variant] = []
        for variant_info in json.loads(self.process.stdout):
            variants.append(Variant(**variant_info))
        return variants

    def get_case(self, case_id: str) -> Optional[ScoutExportCase]:
        """Fetch a case from Scout"""
        cases: List[ScoutExportCase] = self.get_cases(case_id=case_id)
        if not cases:
            return None
        return cases[0]

    def get_cases(
        self,
        case_id: Optional[str] = None,
        reruns: bool = False,
        finished: bool = False,
        status: Optional[str] = None,
        days_ago: int = None,
    ) -> List[ScoutExportCase]:
        """Interact with cases existing in the database."""
        # These commands can be run with `scout export cases`
        get_cases_command = ["export", "cases", "--json"]
        if case_id:
            get_cases_command.extend(["--case-id", case_id])

        elif status:
            get_cases_command.extend(["--status", status])

        elif finished:
            get_cases_command.append("--finished")

        if reruns:
            LOG.info("Fetching cases that are reruns")
            get_cases_command.append("--reruns")

        if days_ago:
            get_cases_command.extend(["--within-days", str(days_ago)])

        try:
            self.process.run_command(get_cases_command)
            if not self.process.stdout:
                return []
        except CalledProcessError:
            LOG.info("Could not find cases")
            return []

        cases = []
        for case_export in json.loads(self.process.stdout):
            LOG.info("Validating case %s", case_export.get("_id"))
            case_obj = ScoutExportCase(**case_export)
            cases.append(case_obj)
        return cases

    def get_solved_cases(self, days_ago: int) -> List[ScoutExportCase]:
        """
        Get cases solved within chosen timespan

        Args:
            days_ago (int): Maximum days ago a case has been solved

        Return:
            cases (list): list of cases
        """
        return self.get_cases(status="solved", days_ago=days_ago)

    def upload_delivery_report(self, report_path: str, case_id: str, update: bool = False) -> None:
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
        upload_delivery_report_command = ["load", "delivery-report", case_id, report_path]
        if update:
            upload_delivery_report_command.append("--update")

        try:
            LOG.info("Uploading delivery report %s to case %s", report_path, case_id)
            self.process.run_command(upload_delivery_report_command)
        except CalledProcessError:
            LOG.warning("Something went wrong when uploading delivery report")
