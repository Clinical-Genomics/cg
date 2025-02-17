from cg.constants.constants import SampleStatus
from cg.exc import AuthorisationError
from cg.server.dto.samples.requests import CollaboratorSamplesRequest, SamplesRequest
from cg.server.dto.samples.samples_response import SamplesResponse
from cg.services.web_services.sample.utils import (
    create_samples_response,
    get_cancel_comment,
    get_confirmation_message,
    get_start_and_finish_indexes_from_request,
)
from cg.store.models import Customer, Sample, User
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
        case_ids = self.store.get_case_ids_for_samples(sample_ids)

        for sample_id in sample_ids:
            self.cancel_sample(sample_id=sample_id, user_email=user_email)

        self.store.delete_cases_without_samples(case_ids)
        remaining_cases = self.store.filter_cases_with_samples(case_ids)
        return get_confirmation_message(sample_ids=sample_ids, case_ids=remaining_cases)

    def get_collaborator_samples(self, request: CollaboratorSamplesRequest) -> SamplesResponse:
        samples: list[Sample] = self.store.get_collaborator_samples(request)
        return create_samples_response(samples)

    def get_samples(self, request: SamplesRequest, user: User) -> tuple[list[dict], int]:
        if request.status in SampleStatus.statuses():
            if not user.is_admin:
                raise AuthorisationError()
            else:
                return self._get_samples_handled_by_status(request=request)
        customers: list[Customer] | None = None if user.is_admin else user.customers
        samples, total = self.store.get_samples_by_customers_and_pattern(
            pattern=request.enquiry,
            customers=customers,
            limit=request.page_size,
            offset=(request.page - 1) * request.page_size,
        )
        parsed_samples: list[dict] = [sample.to_dict() for sample in samples]
        return parsed_samples, total

    def _get_samples_handled_by_status(self, request: SamplesRequest) -> tuple[list[dict], int]:
        """Get samples based on the provided status."""
        if request.status == SampleStatus.INCOMING:
            samples: list[Sample] = self.store.get_samples_to_receive()
        elif request.status == SampleStatus.LABPREP:
            samples: list[Sample] = self.store.get_samples_to_prepare()
        else:
            samples: list[Sample] = self.store.get_samples_to_sequence()
        start, finish = get_start_and_finish_indexes_from_request(request)
        parsed_samples: list[dict] = [sample.to_dict() for sample in samples[start:finish]]
        return parsed_samples, len(parsed_samples)
