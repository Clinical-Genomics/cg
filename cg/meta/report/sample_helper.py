"""Module with Convenience methods for cg samples"""
from cg.store import Store


class SampleHelper:
    """API with Convenience methods for cg samples"""

    def __init__(self, store: Store):
        self._store = store

    def is_ready_made_sample(self, internal_id):
        """Check if sample is a rml sample"""
        return self.get_prep_category(internal_id) == "rml"

    def is_externally_sequenced(self, internal_id):
        """Check if sample is externally sequenced"""
        return self._store.sample(internal_id).application_version.application.is_external

    def get_prep_category(self, internal_id):
        """Get the prep category of the application of the sample"""
        return self._store.sample(internal_id).application_version.application.prep_category

    def is_analysis_sample(self, internal_id):
        """Check if this sample is destined for an analysis"""
        return (
            not self._store.family(internal_id).data_analysis
            or "fastq" not in self._store.family(internal_id).data_analysis
        )
