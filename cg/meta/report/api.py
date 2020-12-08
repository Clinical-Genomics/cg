"""Module to create MIP analysis delivery reports"""
import logging
from datetime import datetime
from pathlib import Path

import requests
import ruamel.yaml
from jinja2 import Environment, PackageLoader, select_autoescape
from cg.apps.coverage import ChanjoAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.meta.report.report_validator import ReportValidator
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.report.sample_calculator import SampleCalculator
from cg.meta.report.report_helper import ReportHelper
from cg.meta.report.presenter import Presenter
from cg.store import Store, models
from cg.exc import DeliveryReportError


class ReportAPI:
    """API to create MIP analysis delivery reports"""

    def __init__(
        self,
        store: Store,
        lims_api: LimsAPI,
        chanjo_api: ChanjoAPI,
        analysis_api: MipAnalysisAPI,
        scout_api: ScoutAPI,
        logger=logging.getLogger(__name__),
        yaml_loader=ruamel.yaml,
        path_tool=Path,
    ):

        self.store = store
        self.lims = lims_api
        self.chanjo = chanjo_api
        self.analysis = analysis_api
        self.log = logger
        self.yaml_loader = yaml_loader
        self.path_tool = path_tool
        self.scout = scout_api
        self.report_validator = ReportValidator(store)

    def create_delivery_report(self, case_id: str, accept_missing_data: bool = False) -> str:
        """Generate the html contents of a delivery report."""

        delivery_data = self._get_delivery_data(case_id)
        self._handle_missing_report_data(accept_missing_data, delivery_data, case_id)
        report_data = self._make_data_presentable(delivery_data)
        self._handle_missing_report_data(accept_missing_data, report_data, case_id)
        rendered_report = self._render_delivery_report(report_data)
        return rendered_report

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

    def create_delivery_report_file(
        self, case_id: str, file_path: Path, accept_missing_data: bool = False
    ):
        """Generate a temporary file containing a delivery report."""

        delivery_report = self.create_delivery_report(
            case_id=case_id, accept_missing_data=accept_missing_data
        )

        file_path.mkdir(parents=True, exist_ok=True)
        report_file_path = Path(file_path / "delivery-report.html")
        delivery_report_file = open(report_file_path, "w")
        delivery_report_file.write(delivery_report)
        delivery_report_file.close()

        return delivery_report_file

    def _get_delivery_data(self, case_id: str) -> dict:
        """Fetch all data needed to render a delivery report."""

        report_data = dict()
        case_obj = self._get_case_from_statusdb(case_id)
        analysis_obj = case_obj.analyses[0]

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

    def _incorporate_trending_data(self, report_data: dict, case_id: str):
        """Incorporate trending data into a set of samples."""
        trending_data = self.analysis.get_latest_metadata(family_id=case_id)

        mapped_reads_all_samples = trending_data.get("mapped_reads", {})
        duplicates_all_samples = trending_data.get("duplicates", {})
        analysis_sex_all_samples = trending_data.get("analysis_sex", {})

        for sample in report_data["samples"]:
            lims_id = sample["internal_id"]
            sample["analysis_sex"] = analysis_sex_all_samples.get(lims_id)
            sample["mapped_reads"] = mapped_reads_all_samples.get(lims_id)
            sample["duplicates"] = duplicates_all_samples.get(lims_id)

        report_data["genome_build"] = trending_data.get("genome_build")

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
