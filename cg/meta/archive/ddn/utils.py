from cg.meta.archive.ddn.constants import MetadataFields
from cg.store.models import Sample


def get_request_log(body: dict):
    return "Sending request with body: \n" + f"{body}"


def get_metadata(sample: Sample) -> list[dict]:
    """Returns metadata generated from a sample."""
    metadata: list[dict] = [
        {
            MetadataFields.NAME.value: MetadataFields.CUSTOMER_NAME.value,
            MetadataFields.VALUE.value: sample.customer.name,
        },
        {
            MetadataFields.NAME.value: MetadataFields.PREP_CATEGORY.value,
            MetadataFields.VALUE.value: sample.prep_category,
        },
        {
            MetadataFields.NAME.value: MetadataFields.SAMPLE_NAME.value,
            MetadataFields.VALUE.value: sample.name,
        },
        {
            MetadataFields.NAME.value: MetadataFields.SEQUENCED_AT.value,
            MetadataFields.VALUE.value: (
                str(sample.last_sequenced_at)
                if sample.last_sequenced_at
                else sample.last_sequenced_at
            ),
        },
        {
            MetadataFields.NAME.value: MetadataFields.TICKET_NUMBER.value,
            MetadataFields.VALUE.value: sample.original_ticket,
        },
    ]
    return metadata
