class MockLimsAPI:
    """Mock LIMS API to get target bed from lims"""

    def __init__(self, config: dict = None):
        self.config = config
        self.sample_vars = {}

    def add_sample(self, internal_id: str):
        self.sample_vars[internal_id] = {}

    def add_capture_kit(self, internal_id: str, capture_kit):
        if not internal_id in self.sample_vars:
            self.add_sample(internal_id)
        self.sample_vars[internal_id]["capture_kit"] = capture_kit

    def capture_kit(self, internal_id: str):
        if internal_id in self.sample_vars:
            return self.sample_vars[internal_id].get("capture_kit")
        return None
