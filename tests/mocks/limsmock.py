from typing import Any

from pydantic.v1 import BaseModel
from typing_extensions import Literal

from cg.apps.lims import LimsAPI


class LimsProject(BaseModel):
    id: str = "1"


class MockReagentType:
    """Mock class for reagent type."""

    def __init__(self, label: str, sequence: str):
        self.label: str = label
        self.sequence: str = sequence


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
    panels: list[str] = None
    comment: str = None
    project: LimsProject = LimsProject()
    received: str = None
    source: str = None
    priority: str = None


class MockLimsAPI(LimsAPI):
    """Mock LIMS API to get target bed from LIMS."""

    def __init__(self, config: dict = None, samples: list[dict] = None):
        if samples is None:
            samples = []
        self.config = config
        self.baseuri = "https://clinical-lims-mock.scilifelab.se"
        self._received_at = None
        self.sample_vars = {}
        self._samples = samples
        self._prep_method = (
            "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free "
            ""
            "DNA)"
        )
        self._sequencing_method = "CG002 - Cluster Generation (HiSeq X)"
        self._delivery_method = "CG002 - Delivery"
        self._source = "cell-free DNA"

    def set_prep_method(self, method: str = "1337:00 Test prep method"):
        """Mock function"""
        self._prep_method = method

    def set_sequencing_method(self, method: str = "1338:00 Test sequencing method"):
        """Mock function"""
        self._prep_method = method

    def sample(self, lims_id: str) -> dict:
        return next((sample for sample in self._samples if sample["id"] == lims_id), {})

    def add_sample(self, internal_id: str):
        self.sample_vars[internal_id] = {}

    def add_capture_kit(self, internal_id: str, capture_kit):
        if internal_id not in self.sample_vars:
            self.add_sample(internal_id)
        self.sample_vars[internal_id]["capture_kit"] = capture_kit

    def capture_kit(self, lims_id: str):
        if lims_id in self.sample_vars:
            return self.sample_vars[lims_id].get("capture_kit")
        return None

    def get_prep_method(self, lims_id: str) -> str:
        return self._prep_method

    def get_sequencing_method(self, lims_id: str) -> str:
        return self._sequencing_method

    def get_delivery_method(self, lims_id: str) -> str:
        return self._delivery_method

    def get_source(self, lims_id: str) -> str | None:
        return self._source

    def get_sample_comment(self, sample_id: str) -> str:
        lims_sample: dict[str, Any] = self.sample(sample_id)
        comment = None
        if lims_sample:
            comment: str = lims_sample.get("comment")
        return comment

    def get_sample_project(self, sample_id: str) -> str | None:
        lims_sample: dict[str, Any] = self.sample(sample_id)
        project_id = None
        if lims_sample:
            project_id: str = lims_sample.get("project").get("id")
        return project_id

    def update_sample(
        self, lims_id: str, sex=None, target_reads: int = None, name: str = None, **kwargs
    ):
        pass  # This is completely mocked out

    def set_samples(self, samples):
        self._samples = samples

    def cache(self):
        pass  # This is completely mocked out

    def get_received_date(self, lims_id: str):
        received_date = None
        for sample in self._samples:
            if sample.internal_id == lims_id:
                received_date = sample.received_at
        return received_date

    def get_sample_rin(self, sample_id: str) -> float:
        """Mock return sample RIN value."""
        return 10.0

    def get_latest_rna_input_amount(self, sample_id: str) -> float:
        """Mock return input amount used in the latest preparation of an RNA sample."""
        return 300.0

    def get_sample_dv200(self, sample_id: str) -> float:
        """Mock return sample's percentage of RNA fragments greater than 200 nucleotides."""
        return 75.0

    def has_sample_passed_initial_qc(self, sample_id: str) -> bool:
        """Mock return of the sample initial QC flag."""
        return True
