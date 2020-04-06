from cg.meta.report.sample_helper import SampleHelper
from cg.store import Store


class ReportValidator:

    def __init__(self, store: Store):
        self._sample_helper = SampleHelper(store)

    def has_required_data(self, report_data: dict):

        if not self._has_all_values(report_data, ["report_version",
                                                  "family",
                                                  "customer_name",
                                                  "today",
                                                  "panels",
                                                  "customer_invoice_address",
                                                  "scout_access",
                                                  "accredited"]):
            return False

        for sample in report_data["samples"]:

            if isinstance(sample, str):
                print(report_data)
                print('t(s)', type(sample))
                print(sample)
                continue

            if not self._sample_helper.is_ready_made_sample(sample["internal_id"]) and \
                    not self._has_all_values(sample, ["prepared_at"]):
                return False

            if self._sample_helper.is_sequence_sample(sample["internal_id"]):
                if not self._has_all_values(sample, ["received_at", "prepared_at",
                                                     "sequenced_at"]):
                    return False

            if not self._has_all_values(sample, ["delivered_at"]):
                return False
        return True

    @staticmethod
    def _has_all_values(subscriptable, keys):
        for key in keys:
            if not subscriptable[key]:
                return False

        return True
