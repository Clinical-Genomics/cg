from cg.store import Store


class SampleHelper:

    def __init__(self, store: Store):
        self._store = store

    def is_ready_made_sample(self, internal_id):
        return self.get_prep_category(internal_id) == "rml"

    def is_sequence_sample(self, internal_id):
        return not self._store.sample(internal_id).is_external

    def get_prep_category(self, internal_id):
        return self._store.sample(internal_id).application_version.application.prep_category
