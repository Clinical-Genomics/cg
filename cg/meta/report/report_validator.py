"""Module to validate that required delivery report data exists"""
from cg.exc import ValidationError
from cg.meta.report.sample_helper import SampleHelper
from cg.store import Store


REQUIRED_REPORT_FIELDS = [
    "report_version",
    "case",
    "customer_name",
    "today",
    "panels",
    "customer_invoice_address",
    "scout_access",
    "accredited",
    "pipeline",
    "pipeline_version",
    "genome_build",
]

REQUIRED_GENERIC_SAMPLE_FIELDS = [
    "name",
    "internal_id",
    "sex",
    "status",
    "ticket",
    "application",
    "ordered_at",
    "received_at",
    "delivered_at",
    "processing_time",
    "analysis_sex",
]

REQUIRED_ANALYSIS_SAMPLE_FIELDS = [
    "mapped_reads",
    "duplicates",
    "analysis_sex",
    "target_coverage",
    "target_completeness",
]


class ReportValidator:
    """API to validate report data"""

    def __init__(self, store: Store):
        self._sample_helper = SampleHelper(store)
        self._attributes_missing_values = None

    def has_required_data(self, report_data: dict, case_id: str) -> bool:
        """Main method to validate report data"""

        self._attributes_missing_values = []

        self._check_required_general_report_data(report_data)

        for sample in report_data["samples"]:
            self._check_required_sample_attributes(sample, case_id)

        return self.get_missing_attributes() == []

    def get_missing_attributes(self) -> [str]:
        """Returns a list of all attributes that seems to be missing in the report data set"""
        if self._attributes_missing_values is None:
            raise ValidationError(
                "get_missing_attributes() can only be run after " "has_required_data(...)"
            )

        return self._attributes_missing_values

    def _collect_missing_attributes(self, a_dict: dict, keys: list) -> None:
        """Gathers all attributes that should exist but is without a value"""
        for key in keys:
            if a_dict.get(key) is None:
                self._attributes_missing_values.append(key)

    def _check_required_sample_attributes_for_all(self, sample: dict) -> None:
        """Checks attributes that should exist on all samples"""
        self._collect_missing_attributes(sample, REQUIRED_GENERIC_SAMPLE_FIELDS)

    def _check_required_sample_attributes(self, sample: dict, case_id: str) -> None:
        """Checks attributes for a sample"""
        self._check_required_sample_attributes_for_all(sample)

        if not sample.get("internal_id"):
            return

        if self._sample_helper.is_ready_made_sample(sample["internal_id"]):
            raise ValidationError("Can't handle RML samples")

        if not self._sample_helper.is_externally_sequenced(sample["internal_id"]):
            self._collect_missing_attributes(
                sample,
                [
                    "prepared_at",
                    "prep_method",
                    "sequencing_method",
                    "sequenced_at",
                    "million_read_pairs",
                    "mapped_reads",
                    "duplicates",
                ],
            )

        if self._sample_helper.is_analysis_sample(case_id):
            self._collect_missing_attributes(sample, REQUIRED_ANALYSIS_SAMPLE_FIELDS)

    def _check_required_general_report_data(self, report_data: dict) -> None:
        """Check root-level attributes for a report data set"""
        self._collect_missing_attributes(report_data, REQUIRED_REPORT_FIELDS)
