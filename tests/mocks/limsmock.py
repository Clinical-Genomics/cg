from typing import List, Optional

from cg.apps.lims import LimsAPI
from pydantic import BaseModel
from typing_extensions import Literal


class LimsSample(BaseModel):
    id: str
    name: str = None
    customer: str = None
    sex: Literal["male", "female", "unknown"] = None
    father: str = None
    mother: str = None
    status: Literal["affected", "unaffected", "unknown"] = None
    application: str = None
    application_version: str = None
    family: str = None
    panels: List[str] = None
    comment: str = None
    project: str = None
    received: str = None
    source: str = None
    priority: str = None


class MockLimsAPI(LimsAPI):
    """Mock LIMS API to get target bed from lims"""

    def __init__(self, config: dict = None, samples: List[dict] = []):
        self.config = config
        self.sample_vars = {}
        self._samples = samples

    def sample(self, sample_id: str) -> Optional[dict]:
        for sample in self._samples:
            if sample["id"] == sample_id:
                return sample
        return None

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

    def get_prep_method(self, lims_id: str) -> str:
        return (
            "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free "
            ""
            "DNA)"
        )

    def get_sequencing_method(self, lims_id: str) -> str:
        return "CG002 - Cluster Generation (HiSeq X)"

    def get_delivery_method(self, lims_id: str) -> str:
        return "CG002 - Delivery"

    def update_sample(
        self, lims_id: str, sex=None, target_reads: int = None, name: str = None, **kwargs
    ):
        pass  # This is completely mocked out
