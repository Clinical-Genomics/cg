from datetime import datetime

from cg.server.dto.samples.samples_response import SampleDTO, SamplesResponse
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


def create_samples_response(samples: list[Sample]) -> SamplesResponse:
    sample_dtos = []
    for sample in samples:
        sample_dtos.append(create_sample_dto(sample))
    return sample_dtos


def create_sample_dto(sample: Sample) -> SampleDTO:
    return SampleDTO(
        name=sample.name,
        internal_id=sample.internal_id,
    )
