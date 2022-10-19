import logging
from datetime import datetime

from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from pathlib import Path

LOG = logging.getLogger(__name__)


class MockMicrosaltAnalysis(MicrosaltAnalysisAPI):
    """Mock a microSALT analysis object"""

    def get_case_path(self, case_id: str):
        """Get case path."""
        case_path_list = [Path(self.root_dir, "result", case_id)]

        return case_path_list
