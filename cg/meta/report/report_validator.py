from cg.meta.report.sample_helper import SampleHelper
from cg.store import Store


REQUIRED_REPORT_FIELDS = [
    "report_version",
    "family",
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
    def __init__(self, store: Store):
        self._sample_helper = SampleHelper(store)
        self._attributes_missing_values = []

    def has_required_data(self, report_data: dict) -> bool:

        self._attributes_missing_values = []

        self._check_required_general_report_data(report_data)

        for sample in report_data["samples"]:
            self._check_required_sample_attributes(sample)

        return self.get_missing_attributes() == []

    def _collect_missing_attributes(self, subscriptable, keys):
        for key in keys:
            if not subscriptable[key]:
                self._attributes_missing_values.append(key)

    def _check_required_sample_attributes_for_all(self, sample):
        self._collect_missing_attributes(sample, REQUIRED_GENERIC_SAMPLE_FIELDS)

    def _check_required_sample_attributes(self, sample):
        self._check_required_sample_attributes_for_all(sample)

        if not sample.get("internal_id"):
            return

        if not self._sample_helper.is_externally_sequenced(sample["internal_id"]):
            self._collect_missing_attributes(
                sample,
                [
                    "sequencing_method",
                    "sequenced_at",
                    "million_read_pairs",
                    "mapped_reads",
                    "duplicates",
                ],
            )

        if not self._sample_helper.is_ready_made_sample(
            sample["internal_id"]
        ) and not self._sample_helper.is_externally_sequenced(sample["internal_id"]):
            self._collect_missing_attributes(sample, ["prepared_at", "prep_method"])

        if self._sample_helper.is_analysis_sample(sample["internal_id"]):
            self._collect_missing_attributes(sample, REQUIRED_ANALYSIS_SAMPLE_FIELDS)

    def _check_required_general_report_data(self, report_data):
        self._collect_missing_attributes(report_data, REQUIRED_REPORT_FIELDS)

    def get_missing_attributes(self) -> [str]:
        return self._attributes_missing_values
