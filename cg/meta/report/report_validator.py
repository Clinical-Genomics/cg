from cg.meta.report.sample_helper import SampleHelper
from cg.store import Store


class ReportValidator:
    def __init__(self, store: Store):
        self._sample_helper = SampleHelper(store)

    def has_required_data(self, report_data: dict) -> bool:

        if not self._required_general_report_data(report_data):
            return False

        for sample in report_data["samples"]:

            if isinstance(sample, str):
                print(report_data)
                print("t(s)", type(sample))
                print(sample)
                continue

            if not self._has_required_sample_values(sample):
                return False

        return True

    @staticmethod
    def _has_all_values(subscriptable, keys) -> bool:
        for key in keys:
            if not subscriptable[key]:
                return False

        return True

    def _has_required_values_for_all_samples(self, sample) -> bool:
        return self._has_all_values(
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

    def _has_required_sample_values(self, sample) -> bool:
        if not self._has_required_values_for_all_samples(sample):
            return False

        if not self._sample_helper.is_ready_made_sample(
            sample["internal_id"]
        ) and not self._has_all_values(sample, ["prepared_at", "prep_method"]):
            return False

        if self._sample_helper.is_sequence_sample(sample["internal_id"]):
            if not self._has_all_values(
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
            ):
                return False

        return True

    def _required_general_report_data(self, report_data) -> bool:
        return self._has_all_values(
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
