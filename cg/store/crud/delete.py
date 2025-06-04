"""Handler to delete data objects."""

from cg.store.crud.read import ReadHandler
from cg.store.models import Case, OrderTypeApplication, Sample


class DeleteMixin(ReadHandler):
    """Contains methods to delete business data model instances."""

    def delete_cases_without_samples(self, case_internal_ids: list[str]) -> None:
        """Delete any cases specified in case_ids without samples."""
        for case_internal_id in case_internal_ids:
            case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
            if case and not case.links:
                self.delete_item_from_store(case)
        self.commit_to_store()

    def delete_illumina_flow_cell(self, internal_id: str):
        """Delete an Illumina flow cell."""

        if flow_cell := self.get_illumina_flow_cell_by_internal_id(internal_id=internal_id):
            self.delete_item_from_store(flow_cell)
            self.commit_to_store()

    def decouple_sample_from_cases(self, sample_id: int) -> None:
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        for case_sample in sample.links:
            self.delete_item_from_store(case_sample)
        self.commit_to_store()

    def delete_order_type_applications_by_application_id(self, application_id: int) -> None:
        self._get_query(OrderTypeApplication).filter_by(application_id=application_id).delete()
