"""Module to create delivery reports"""

from datetime import datetime
import logging
from pathlib import Path
from typing import TextIO, Optional

import housekeeper
from cg.meta.workflow.analysis import AnalysisAPI
from cg.constants.tags import HK_DELIVERY_REPORT_TAG
from cg.models.cg_config import CGConfig
from cg.meta.meta import MetaAPI
from cg.store import models
from jinja2 import Environment, PackageLoader, select_autoescape

LOG = logging.getLogger(__name__)


class ReportAPI(MetaAPI):
    """Parent class of existing report APIs"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api = analysis_api

    def create_delivery_report(
        self, case_id: str, analysis_date: datetime, force_report: bool = False
    ) -> str:
        """Generates the html contents of a delivery report"""

        report_data = self.get_report_data(
            case_id=case_id, analysis_date=analysis_date, force_report=force_report
        )
        rendered_report = self.render_delivery_report(report_data)
        return rendered_report

    def create_delivery_report_file(
        self, case_id: str, file_path: Path, analysis_date: datetime, force_report: bool = False
    ) -> TextIO:
        """Generates a temporary file containing a delivery report"""

        file_path.mkdir(parents=True, exist_ok=True)
        delivery_report = self.create_delivery_report(
            case_id=case_id, analysis_date=analysis_date, force_report=force_report
        )

        report_file_path = Path(file_path / "delivery-report.html")
        with open(report_file_path, "w") as delivery_report_file:
            delivery_report_file.write(delivery_report)

        return delivery_report_file

    def add_delivery_report_to_hk(
        self, delivery_report_file: Path, case_id: str, analysis_date: datetime
    ) -> Optional[housekeeper.store.models.File]:
        """
        Adds a delivery report file, if it has not already been generated, to an analysis bundle for a specific case
        in HK and returns a pointer to it
        """

        version = self.housekeeper_api.version(case_id, analysis_date)
        try:
            self.get_delivery_report_from_hk(case_id=case_id)
        except FileNotFoundError:
            file = self.housekeeper_api.add_file(
                delivery_report_file.name, version, HK_DELIVERY_REPORT_TAG
            )
            self.housekeeper_api.include_file(file, version)
            self.housekeeper_api.add_commit(file)
            return file

        return None

    def get_delivery_report_from_hk(self, case_id: str) -> str:
        """Extracts the delivery reports of a specific case stored in HK"""

        version = self.housekeeper_api.last_version(case_id)
        delivery_report_files = self.housekeeper_api.get_files(
            bundle=case_id, tags=[HK_DELIVERY_REPORT_TAG], version=version.id
        )

        if delivery_report_files.count() == 0:
            raise FileNotFoundError(f"No delivery report was found in housekeeper for {case_id}")

        return delivery_report_files[0].full_path

    def get_report_data(
        self, case_id: str, analysis_date: datetime, force_report: bool = False
    ) -> dict:
        """Fetches all the data needed to generate a delivery report"""

        raise NotImplementedError

    def render_delivery_report(self, report_data: dict) -> str:
        """Renders the report on the Jinja template"""

        env = Environment(
            loader=PackageLoader("cg", "meta/report/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(f"{self.analysis_api.pipeline}_report.html")
        return template.render(**report_data)

    def get_cases_without_delivery_report(self):
        """Returns a list of analyses that need a delivery report"""

        return self.status_db.analyses_to_delivery_report(self.analysis_api.pipeline)[:50]

    def get_genes_from_scout(self, panels: list) -> list:
        """Extracts panel gene IDs information from Scout"""

        panel_genes = list()
        for panel in panels:
            panel_genes.extend(self.scout_api.get_genes(panel))

        panel_gene_ids = [gene.get("hgnc_id") for gene in panel_genes]
        return panel_gene_ids

    @staticmethod
    def get_report_version(analysis: models.Analysis) -> int:
        """
        Returns the version of the given analysis. The version of the first analysis is 1. Subsequent reruns
        increase the version by 1.
        """

        version = None
        if analysis:
            version = len(analysis.family.analyses) - analysis.family.analyses.index(analysis)

        return version

    @staticmethod
    def get_previous_report_version(analysis: models.Analysis) -> int:
        """Returns the analysis version prior to the given one"""

        analysis_version = ReportAPI.get_report_version(analysis)
        previous_version = None

        if analysis_version and analysis_version > 1:
            previous_version = analysis_version - 1

        return previous_version

    @staticmethod
    def get_days_to_deliver_sample(sample: models.Sample):
        """Returns the days it takes to deliver a sample"""

        if sample.received_at and sample.delivered_at:
            return (sample.delivered_at - sample.received_at).days

        return None


'''

    @staticmethod
    def update_delivery_report_date(
        status_api: Store, case_id: str, analysis_date: datetime
    ) -> None:
        """Update date on analysis when delivery report was created"""

        case_obj = status_api.family(case_id)
        analysis_obj = status_api.analysis(case_obj, analysis_date)
        analysis_obj.delivery_report_created_at = datetime.now()
        status_api.commit()


'''
