"""Module to create MIP analysis delivery reports"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO, Union

import housekeeper
import requests
from cg.apps.coverage import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.exc import DeliveryReportError
from cg.meta.report.presenter import Presenter
from cg.meta.report.report_helper import ReportHelper
from cg.meta.report.report_validator import ReportValidator
from cg.meta.report.sample_calculator import SampleCalculator
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric
from cg.store import Store, models
from jinja2 import Environment, PackageLoader, select_autoescape


class ReportAPI:
    """API to create MIP analysis delivery reports"""

    def __init__(
        self,
        store: Store,
        lims_api: LimsAPI,
        chanjo_api: ChanjoAPI,
        analysis_api: AnalysisAPI,
        scout_api: ScoutAPI,
        logger=logging.getLogger(__name__),
        path_tool=Path,
    ):

        self.store = store
        self.lims = lims_api
        self.chanjo = chanjo_api
        self.analysis = analysis_api
        self.log = logger
        self.path_tool = path_tool
        self.scout = scout_api
        self.report_validator = ReportValidator(store)

    def create_delivery_report(
        self, case_id: str, analysis_date: datetime, accept_missing_data: bool = False
    ) -> str:
        """Generate the html contents of a delivery report."""

        delivery_data = self._get_delivery_data(case_id=case_id, analysis_date=analysis_date)
        self._handle_missing_report_data(accept_missing_data, delivery_data, case_id)
        report_data = self._make_data_presentable(delivery_data)
        self._handle_missing_report_data(accept_missing_data, report_data, case_id)
        rendered_report = self._render_delivery_report(report_data)
        return rendered_report

    def create_delivery_report_file(
        self,
        case_id: str,
        file_path: Path,
        analysis_date: datetime,
        accept_missing_data: bool = False,
    ) -> TextIO:
        """Generate a temporary file containing a delivery report."""

        delivery_report = self.create_delivery_report(
            case_id=case_id, accept_missing_data=accept_missing_data, analysis_date=analysis_date
        )
        file_path.mkdir(parents=True, exist_ok=True)
        report_file_path = Path(file_path / "delivery-report.html")
        with open(report_file_path, "w") as delivery_report_file:
            delivery_report_file.write(delivery_report)

        return delivery_report_file

    def add_delivery_report_to_hk(
        self,
        delivery_report_file: Path,
        hk_api: HousekeeperAPI,
        case_id: str,
        analysis_date: datetime,
    ) -> Optional[housekeeper.store.models.File]:
        """
        Add a delivery report to a analysis bundle for a case in Housekeeper

        If there is already a delivery report for the bundle doesn't add to it
        If successful the method returns a pointer to the new file in Housekeeper
        """
        delivery_report_tag_name = "delivery-report"

        version_obj = hk_api.version(case_id, analysis_date)

        is_bundle_missing_delivery_report = False
        try:
            self.get_delivery_report_from_hk(hk_api=hk_api, case_id=case_id)
        except FileNotFoundError:
            is_bundle_missing_delivery_report = True

        if is_bundle_missing_delivery_report:
            file_obj = hk_api.add_file(
                delivery_report_file.name, version_obj, delivery_report_tag_name
            )
            hk_api.include_file(file_obj, version_obj)
            hk_api.add_commit(file_obj)
            return file_obj

        return None

    @staticmethod
    def get_delivery_report_from_hk(hk_api: HousekeeperAPI, case_id: str) -> str:
        delivery_report_tag_name = "delivery-report"
        version_obj = hk_api.last_version(case_id)
        uploaded_delivery_report_files = hk_api.get_files(
            bundle=case_id,
            tags=[delivery_report_tag_name],
            version=version_obj.id,
        )

        if uploaded_delivery_report_files.count() == 0:
            raise FileNotFoundError(f"No delivery report was found in housekeeper for {case_id}")

        return uploaded_delivery_report_files[0].full_path

    @staticmethod
    def update_delivery_report_date(
        status_api: Store, case_id: str, analysis_date: datetime
    ) -> None:
        """Update date on analysis when delivery report was created"""

        case_obj = status_api.family(case_id)
        analysis_obj = status_api.analysis(case_obj, analysis_date)
        analysis_obj.delivery_report_created_at = datetime.now()
        status_api.commit()

    def _handle_missing_report_data(self, accept_missing_data, delivery_data, case_id):
        """Handle when some crucial data is missing in the report"""
        if not self.report_validator.has_required_data(delivery_data, case_id):
            if not accept_missing_data:
                raise DeliveryReportError(
                    f"Could not generate report data for {case_id}, "
                    f"missing data:"
                    f" {self.report_validator.get_missing_attributes()}"
                )

            self.log.warning(
                "missing data: %s", ", ".join(self.report_validator.get_missing_attributes())
            )

    def _get_delivery_data(self, case_id: str, analysis_date: datetime) -> dict:
        """Fetch all data needed to render a delivery report."""

        report_data = dict()
        case_obj = self._get_case_from_statusdb(case_id)
        analysis_obj = self._get_analysis_from_statusdb(case_obj, analysis_date)

        report_data["case"] = case_obj.name
        report_data["pipeline"] = analysis_obj.pipeline
        report_data["pipeline_version"] = analysis_obj.pipeline_version
        report_data["customer_name"] = case_obj.customer.name
        report_data["customer_internal_id"] = case_obj.customer.internal_id
        report_data["customer_invoice_address"] = case_obj.customer.invoice_address
        report_data["scout_access"] = bool(case_obj.customer.scout_access)
        report_data["report_version"] = ReportHelper.get_report_version(analysis_obj)
        report_data["previous_report_version"] = ReportHelper.get_previous_report_version(
            analysis_obj
        )

        report_data["samples"] = self._fetch_case_samples_from_status_db(case_id)
        report_data["panels"] = self._fetch_panels_from_status_db(case_id)
        self._incorporate_lims_data(report_data)
        self._incorporate_lims_methods(report_data["samples"])
        self._incorporate_coverage_data(report_data["samples"], report_data["panels"])
        self._incorporate_trending_data(report_data, case_id)

        report_data["today"] = datetime.today()
        application_data = self._get_application_data_from_status_db(report_data["samples"])
        report_data.update(application_data)
        return report_data

    def _get_case_from_statusdb(self, case_id: str) -> models.Family:
        """Fetch a case object from the status database."""
        return self.store.family(case_id)

    def _get_analysis_from_statusdb(
        self, case: models.Family, analysis_date: datetime
    ) -> models.Analysis:
        """Fetch an analysis object from the status database."""
        return self.store.analysis(case, analysis_date)

    def _incorporate_lims_methods(self, samples: list):
        """Fetch the methods used for preparation, sequencing and delivery of the samples."""

        for sample in samples:
            lims_id = sample["internal_id"]
            method_types = ["prep_method", "sequencing_method"]
            for method_type in method_types:
                get_method = getattr(self.lims, f"get_{method_type}")
                method_name = get_method(lims_id)
                sample[method_type] = method_name

    @staticmethod
    def _render_delivery_report(report_data: dict) -> str:
        """Render and return report data on the report Jinja template."""

        env = Environment(
            loader=PackageLoader("cg", "meta/report/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report.html")
        template_out = template.render(**report_data)
        return template_out

    def _get_sample_coverage_from_chanjo(self, lims_id: str, genes: list) -> dict:

        """Get coverage data from Chanjo for a sample."""
        return self.chanjo.sample_coverage(lims_id, genes)

    def _incorporate_trending_data(self, report_data: dict, case_id: str) -> None:
        """Incorporate trending data into a set of samples."""
        mip_analysis: Union[MipAnalysis, None] = self.analysis.get_latest_metadata(
            family_id=case_id
        )

        if not mip_analysis:
            return
        for sample in report_data["samples"]:
            sample_id_metric = get_sample_id_metric(
                sample_id=sample["internal_id"], sample_id_metrics=mip_analysis.sample_id_metrics
            )
            sample["analysis_sex"] = sample_id_metric.predicted_sex
            sample["duplicates"] = sample_id_metric.duplicate_reads
            sample["mapped_reads"] = sample_id_metric.mapped_reads

        report_data["genome_build"] = mip_analysis.genome_build

    def _incorporate_coverage_data(self, samples: list, panels: list):
        """Incorporate coverage data from Chanjo for each sample ."""

        genes = self._get_genes_from_scout(panels)

        for sample in samples:
            lims_id = sample["internal_id"]

            sample_coverage = self._get_sample_coverage_from_chanjo(lims_id, genes)

            target_coverage = None
            target_completeness = None

            if sample_coverage:
                target_coverage = sample_coverage.get("mean_coverage")
                target_completeness = sample_coverage.get("mean_completeness")
            else:
                self.log.warning("No coverage could be calculated for: %s", lims_id)

            sample["target_coverage"] = target_coverage
            sample["target_completeness"] = target_completeness

    def _fetch_case_samples_from_status_db(self, case_id: str) -> list:
        """Incorporate data from the status database for each sample ."""

        delivery_data_samples = list()
        case_samples = self.store.family_samples(case_id)
        case = self.store.family(case_id)

        for case_sample in case_samples:
            sample = case_sample.sample
            delivery_data_sample = dict()
            delivery_data_sample["internal_id"] = sample.internal_id
            delivery_data_sample["ticket"] = sample.ticket_number
            delivery_data_sample["status"] = case_sample.status
            delivery_data_sample["received_at"] = sample.received_at
            delivery_data_sample["prepared_at"] = sample.prepared_at
            delivery_data_sample["sequenced_at"] = sample.sequenced_at
            delivery_data_sample["delivered_at"] = sample.delivered_at
            delivery_data_sample["processing_time"] = SampleCalculator.calculate_processing_days(
                sample
            )
            delivery_data_sample["ordered_at"] = sample.ordered_at
            delivery_data_sample["million_read_pairs"] = (
                round(sample.reads / 2000000, 1) if sample.reads else None
            )

            delivery_data_sample["capture_kit"] = sample.capture_kit
            delivery_data_sample["data_analysis"] = case.data_analysis
            delivery_data_samples.append(delivery_data_sample)

        return delivery_data_samples

    def _get_application_data_from_status_db(self, samples: list) -> dict:
        """Fetch application data including accreditation status for all samples."""
        application_data = dict()
        used_applications = set()

        for sample in samples:
            used_applications.add((sample["application"], sample["application_version"]))

        applications = []
        accreditations = []
        for apptag_id, apptag_version in used_applications:

            application_is_accredited = False

            application = self.store.application(tag=apptag_id)

            if application:
                application_is_accredited = application.is_accredited
                applications.append(
                    {
                        "tag": application.tag,
                        "description": application.description,
                        "limitations": application.limitations,
                    }
                )

            accreditations.append(application_is_accredited)

        application_data["applications"] = applications
        application_data["accredited"] = bool(all(accreditations))

        return application_data

    def _fetch_panels_from_status_db(self, case_id: str) -> list:
        """fetch data from the status database for each panels ."""
        case_obj = self.store.family(case_id)
        panels = case_obj.panels
        return panels

    def _incorporate_lims_data(self, report_data: dict):
        """Incorporate data from LIMS for each sample ."""
        for sample in report_data.get("samples"):
            lims_id = sample["internal_id"]

            try:
                lims_sample = self.lims.sample(lims_id)
            except requests.exceptions.HTTPError as error:
                lims_sample = dict()
                self.log.info("could not fetch sample %s from LIMS: %s", lims_id, error)

            sample["name"] = lims_sample.get("name")
            sample["sex"] = lims_sample.get("sex")
            sample["source"] = lims_sample.get("source")
            sample["application"] = lims_sample.get("application")
            sample["application_version"] = lims_sample.get("application_version")

    def _get_genes_from_scout(self, panels: list) -> list:
        panel_genes = list()

        for panel in panels:
            panel_genes.extend(self.scout.get_genes(panel))

        panel_gene_ids = [gene.get("hgnc_id") for gene in panel_genes]

        return panel_gene_ids

    @staticmethod
    def _make_data_presentable(delivery_data: dict) -> dict:
        """Replace db values with what a human might expect"""

        presenter = Presenter(precision=2)

        _presentable_dict = presenter.process_dict(delivery_data)
        _presentable_dict["accredited"] = delivery_data["accredited"]
        _presentable_dict["scout_access"] = delivery_data["accredited"]

        for sample in delivery_data["samples"]:
            sample["mapped_reads"] = presenter.process_float_string(sample["mapped_reads"], 2)
            sample["target_coverage"] = presenter.process_float_string(sample["target_coverage"], 1)
            sample["target_completeness"] = presenter.process_float_string(
                sample["target_completeness"], 2
            )
            sample["duplicates"] = presenter.process_float_string(sample["duplicates"], 1)

        return _presentable_dict
