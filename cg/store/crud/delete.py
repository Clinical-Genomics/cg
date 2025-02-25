"""Handler to delete data objects"""

from sqlalchemy.orm import Session

from cg.store.base import BaseHandler
from cg.store.models import Case, OrderTypeApplication, Sample


class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def delete_cases_without_samples(self, case_internal_ids: list[str]) -> None:
        """Delete any cases specified in case_ids without samples."""
        for case_internal_id in case_internal_ids:
            case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
            if case and not case.links:
                self.session.delete(case)
        self.session.commit()

    def delete_illumina_flow_cell(self, internal_id: str):
        """Delete an Illumina flow cell."""

        if flow_cell := self.get_illumina_flow_cell_by_internal_id(internal_id=internal_id):
            self.session.delete(flow_cell)
            self.session.commit()

    def decouple_sample_from_cases(self, sample_id: int) -> None:
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        for case_sample in sample.links:
            self.session.delete(case_sample)
        self.session.commit()

    def delete_order_type_applications_by_application_id(self, application_id: int) -> None:
        self._get_query(OrderTypeApplication).filter_by(application_id=application_id).delete()
