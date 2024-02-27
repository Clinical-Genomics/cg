"""Module for the collect qc metrics meta api."""

from cg.meta.meta import MetaAPI


class CollectQCMetricsAPI(MetaAPI):
    """Collect qc metrics API."""

    def get_completed_cases(self):
        completed_cases = self.trailblazer_api.g
