from datetime import datetime
import logging
from typing import Union

import requests
from cg.meta.report.presenter import Presenter
from cg.meta.report.mip_report_validator import MipReportValidator
from cg.exc import DeliveryReportError
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric

LOG = logging.getLogger(__name__)


class MipDNAReportAPI(ReportAPI):
    """API to create Rare disease DNA delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: MipDNAAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.anaysis_api = analysis_api
        self.report_validator = MipReportValidator(self.status_db)

    def get_report_data(
        self, case_id: str, analysis_date: datetime, force_report: bool = False
    ) -> dict:
        """Fetches all the data needed to generate a delivery report"""

        report_data = dict()
        case_obj = self.status_db.family(case_id)
        analysis_obj = self.status_db.analysis(case_obj, analysis_date)

        report_data["case"] = case_obj.name
        report_data["pipeline"] = analysis_obj.pipeline
        report_data["pipeline_version"] = analysis_obj.pipeline_version
        report_data["customer_name"] = case_obj.customer.name
        report_data["customer_internal_id"] = case_obj.customer.internal_id
        report_data["customer_invoice_address"] = case_obj.customer.invoice_address
        report_data["scout_access"] = bool(case_obj.customer.scout_access)
        report_data["report_version"] = self.get_report_version(analysis_obj)
        report_data["previous_report_version"] = self.get_previous_report_version(analysis_obj)
        report_data["panels"] = case_obj.panels
        report_data["samples"] = self.get_case_samples_from_status_db(case_id)
        report_data["samples"] = self.add_lims_data_to_samples(report_data["samples"])
        report_data["samples"] = self.add_lims_methods_to_samples(report_data["samples"])
        report_data["samples"] = self.add_coverage_data_to_samples(
            report_data["samples"], report_data["panels"]
        )
        report_data = self.add_trending_data_to_report(report_data, case_id)
        report_data.update(self.get_application_data_from_status_db(report_data["samples"]))
        report_data["today"] = datetime.today()

        self.handle_missing_data(report_data, case_id, force_report)
        report_data = self.make_data_presentable(report_data)
        self.handle_missing_data(report_data, case_id, force_report)

        return report_data

    def get_case_samples_from_status_db(self, case_id: str) -> list:
        """Retrieves generic information from Status DB of each sample associated to a specific case ID"""

        report_samples = list()
        case_samples = self.status_db.family_samples(case_id)
        case = self.status_db.family(case_id)

        for case_sample in case_samples:
            sample = case_sample.sample
            sample_dict = dict()
            sample_dict["internal_id"] = sample.internal_id
            sample_dict["ticket"] = sample.ticket_number
            sample_dict["status"] = case_sample.status
            sample_dict["received_at"] = sample.received_at
            sample_dict["prepared_at"] = sample.prepared_at
            sample_dict["sequenced_at"] = sample.sequenced_at
            sample_dict["delivered_at"] = sample.delivered_at
            sample_dict["processing_time"] = self.get_days_to_deliver_sample(sample)
            sample_dict["ordered_at"] = sample.ordered_at
            sample_dict["million_read_pairs"] = (
                round(sample.reads / 2000000, 1) if sample.reads else None
            )
            sample_dict["capture_kit"] = sample.capture_kit
            sample_dict["data_analysis"] = case.data_analysis
            report_samples.append(sample_dict)

        return report_samples

    def add_lims_data_to_samples(self, samples: dict) -> dict:
        """Adds data from LIMS to each sample included in the report"""

        for sample in samples:
            lims_id = sample["internal_id"]
            try:
                lims_sample = self.lims_api.sample(lims_id)
            except requests.exceptions.HTTPError as error:
                lims_sample = dict()
                LOG.info("Could not fetch sample %s from LIMS: %s", lims_id, error)

            sample["name"] = lims_sample.get("name")
            sample["sex"] = lims_sample.get("sex")
            sample["source"] = lims_sample.get("source")
            sample["application"] = lims_sample.get("application")
            sample["application_version"] = lims_sample.get("application_version")

        return samples

    def add_lims_methods_to_samples(self, samples: list) -> dict:
        """Adds preparation and sequencing methods to each of the given samples"""

        for sample in samples:
            lims_id = sample["internal_id"]
            method_types = ["prep_method", "sequencing_method"]
            for method_type in method_types:
                get_method = getattr(self.lims_api, f"get_{method_type}")
                method_name = get_method(lims_id)
                sample[method_type] = method_name

        return samples

    def add_coverage_data_to_samples(self, samples: list, panels: list) -> dict:
        """Incorporates coverage data from Chanjo to each sample"""

        genes = self.get_genes_from_scout(panels)
        for sample in samples:
            lims_id = sample["internal_id"]
            sample_coverage = self.chanjo_api.sample_coverage(lims_id, genes)
            target_coverage = None
            target_completeness = None

            if sample_coverage:
                target_coverage = sample_coverage.get("mean_coverage")
                target_completeness = sample_coverage.get("mean_completeness")
            else:
                LOG.warning("No coverage could be calculated for: %s", lims_id)

            sample["target_coverage"] = target_coverage
            sample["target_completeness"] = target_completeness

        return samples

    def add_trending_data_to_report(self, report_data: dict, case_id: str) -> dict:
        """Incorporates MIP trending data into a set of samples of a given report"""

        mip_analysis: Union[MipAnalysis, None] = self.anaysis_api.get_latest_metadata(
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

        return report_data

    def get_application_data_from_status_db(self, samples: list) -> dict:
        """Fetches application data for a given list of samples"""

        application_data = dict()
        used_applications = set()

        for sample in samples:
            used_applications.add((sample["application"], sample["application_version"]))

        applications = []
        accreditations = []
        for apptag_id, apptag_version in used_applications:
            application_is_accredited = False
            application = self.status_db.application(tag=apptag_id)
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

    def handle_missing_data(self, report_data, case_id, force_report):
        """Handles missing data in the delivery report"""

        if not self.report_validator.has_required_data(report_data, case_id):
            if not force_report:
                raise DeliveryReportError(
                    f"Unable to generate the delivery report for {case_id}. Missing data: "
                    f"{self.report_validator.get_missing_attributes()}"
                )

            LOG.warning(
                "Missing data: %s", ", ".join(self.report_validator.get_missing_attributes())
            )

    @staticmethod
    def make_data_presentable(delivery_data: dict) -> dict:
        """Replaces DB fetched values with what a human might expect"""

        presenter = Presenter(precision=2)
        presentable_dict = presenter.process_dict(delivery_data)
        presentable_dict["accredited"] = delivery_data["accredited"]
        presentable_dict["scout_access"] = delivery_data["accredited"]

        for sample in delivery_data["samples"]:
            sample["mapped_reads"] = presenter.process_float_string(sample["mapped_reads"], 2)
            sample["target_coverage"] = presenter.process_float_string(sample["target_coverage"], 1)
            sample["target_completeness"] = presenter.process_float_string(
                sample["target_completeness"], 2
            )
            sample["duplicates"] = presenter.process_float_string(sample["duplicates"], 1)

        return presentable_dict
