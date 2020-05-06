"""Mock the madeline API"""

from cg.apps.madeline.api import MadelineAPI


class MockMadelineAPI(MadelineAPI):
    """Mock the madeline api methods"""

    def __init__(self):
        """Init mock"""
        self._madeline_outpath = None

    def run(self, family_id, samples, out_path=None):
        """Fetch version from the database."""
        return self._madeline_outpath
