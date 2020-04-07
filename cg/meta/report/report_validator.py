from cg.meta.report.sample_helper import SampleHelper
from cg.store import Store


class ReportValidator:
    def __init__(self, store: Store):
        self._sample_helper = SampleHelper(store)
        self._attributes_missing_values = []

    def has_required_data(self, report_data: dict) -> bool:

        self._attributes_missing_values = []

        self._check_required_general_report_data(report_data)

        for sample in report_data["samples"]:

            if isinstance(sample, str):
                print(report_data)
                print("t(s)", type(sample))
                print(sample)
                continue

            self._check_required_sample_attributes(sample)

        return self.get_missing_attributes() == []

    def _collect_missing_attributes(self, subscriptable, keys):
        for key in keys:
            if not subscriptable[key]:
                self._attributes_missing_values.append(key)

    def _check_required_sample_attributes_for_all(self, sample):
        self._collect_missing_attributes(
            sample,
            [
                "name",
                "internal_id",
                "sex",
                "status",
                "ticket",
                "application",
                "ordered_at",
                "delivery_method",
                "delivered_at",
                "processing_time",
                "data_analysis",
                "analysis_sex",
            ],
        )

    def _check_required_sample_attributes(self, sample):
        self._check_required_sample_attributes_for_all(sample)

        if sample.get("internal_id") and not self._sample_helper.is_ready_made_sample(
            sample["internal_id"]
        ):
            self._collect_missing_attributes(sample, ["prepared_at", "prep_method"])

        if sample.get("internal_id") and self._sample_helper.is_sequence_sample(
            sample["internal_id"]
        ):
            self._collect_missing_attributes(
                sample,
                [
                    "received_at",
                    "prep_method",
                    "prepared_at",
                    "sequencing_method",
                    "sequenced_at",
                    "million_read_pairs",
                    "mapped_reads",
                    "target_coverage",
                    "target_completeness",
                    "duplicates",
                ],
            )

    def _check_required_general_report_data(self, report_data):
        self._collect_missing_attributes(
            report_data,
            [
                "report_version",
                "family",
                "customer_name",
                "today",
                "panels",
                "customer_invoice_address",
                "scout_access",
                "accredited",
                "pipeline_version",
                "genome_build",
            ],
        )

    def get_missing_attributes(self) -> [str]:
        return self._attributes_missing_values
