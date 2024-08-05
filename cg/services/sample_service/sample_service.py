from cg.services.sample_service.utils import (
    get_cancel_comment,
    get_confirmation_message,
)
from cg.store.models import User
from cg.store.store import Store


class SampleService:

    def __init__(self, store: Store):
        self.store = store

    def cancel_sample(self, sample_id: int, user_email: str) -> None:
        self.store.mark_sample_as_cancelled(sample_id)
        self.store.decouple_sample_from_cases(sample_id)
        self._add_cancel_comment(sample_id=sample_id, user_email=user_email)

    def _add_cancel_comment(self, sample_id: int, user_email: str) -> None:
        if user := self.store.get_user_by_email(user_email):
            comment = get_cancel_comment(user.name)
            self.store.update_sample_comment(sample_id=sample_id, comment=comment)

    def cancel_samples(self, sample_ids: list[int], user_email: str) -> str:
        """Returns a cancellation confirmation message."""
        case_ids = self.store.get_case_ids_for_samples(sample_ids)

        for sample_id in sample_ids:
            self.cancel_sample(sample_id=sample_id, user_email=user_email)

        self.store.delete_cases_without_samples(case_ids)
        remaining_cases = self.store.filter_cases_with_samples(case_ids)

        return get_confirmation_message(sample_ids=sample_ids, case_ids=remaining_cases)
