"""Mock the madeline API"""

from cg.apps.madeline.api import MadelineAPI


class MockMadelineAPI(MadelineAPI):
    """Mock the madeline api methods"""

    def __init__(self):
        """Init mock"""
        self._madeline_outpath = None

    # Mock specific functions
    def set_outpath(self, out_path: str) -> None:
        """Set the out path for mock result"""
        self._madeline_outpath = out_path

    # Mocked functions
    def run(self, family_id, samples, out_path=None):
        """Fetch version from the database."""
        return self._madeline_outpath
