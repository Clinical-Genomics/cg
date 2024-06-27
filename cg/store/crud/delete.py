"""Handler to delete data objects"""

from sqlalchemy.orm import Session

from cg.store.base import BaseHandler
from cg.store.filters.status_flow_cell_filters import (
    FlowCellFilter,
    apply_flow_cell_filter,
)
from cg.store.models import Case, Flowcell, Sample, SampleLaneSequencingMetrics, IlluminaFlowCell



class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def delete_relationships_sample(self, sample: Sample) -> None:
        """Delete relationships between all cases and the provided sample."""
        if sample and sample.links:
            for case_sample in sample.links:
                self.session.delete(case_sample)
            self.session.commit()

    def delete_cases_without_samples(self, case_internal_ids: list[str]) -> None:
        """Delete any cases specified in case_ids without samples."""
        for case_internal_id in case_internal_ids:
            case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
            if case and not case.links:
                self.session.delete(case)
        self.session.commit()
