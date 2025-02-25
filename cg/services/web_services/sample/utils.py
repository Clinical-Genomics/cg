from datetime import datetime

from cg.server.dto.samples.requests import SamplesRequest
from cg.server.dto.samples.samples_response import SamplesResponse
from cg.services.web_services.sample.dto_mappers import create_sample_dto
from cg.store.models import Sample


def get_cancel_comment(user_name: str) -> str:
    date: str = datetime.now().strftime("%Y-%m-%d")
    return f"Cancelled {date} by {user_name}"


def get_confirmation_message(sample_ids: list[str], case_ids: list[str]) -> str:
    message = f"Cancelled {len(sample_ids)} samples. "
    if case_ids:
        cases = ", ".join(case_ids)
        message += f"Found {len(case_ids)} cases with additional samples: {cases}."
    else:
        message += "No case contained additional samples."
    return message


def get_start_and_finish_indexes_from_request(request: SamplesRequest) -> tuple[int, int]:
    """
    Return the start and finish indexes to slice a sample list given the pagination information
    in the sample request.
    """
    page_size = request.page_size or 50
    page = request.page or 1
    start = (page - 1) * page_size
    finish = start + page_size
    return start, finish


def create_samples_response(samples: list[Sample]) -> SamplesResponse:
    sample_dtos = []
    for sample in samples:
        sample_dtos.append(create_sample_dto(sample))
    return SamplesResponse(samples=sample_dtos, total=len(samples))
