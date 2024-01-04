from cg.meta.archive.ddn.constants import (
    METADATA_FIELD_NAME,
    METADATA_FIELD_VALUE,
    MetadataFields,
)
from cg.store.models import Sample


def get_metadata(sample: Sample) -> list[dict]:
    """Returns metadata generated from a sample."""
    metadata: list[dict] = [
        {
            METADATA_FIELD_NAME: MetadataFields.CUSTOMER_NAME.value,
            METADATA_FIELD_VALUE: sample.customer.name,
        },
        {
            METADATA_FIELD_NAME: MetadataFields.PREP_CATEGORY.value,
            METADATA_FIELD_VALUE: sample.prep_category,
        },
        {METADATA_FIELD_NAME: MetadataFields.SAMPLE_NAME.value, METADATA_FIELD_VALUE: sample.name},
        {
            METADATA_FIELD_NAME: MetadataFields.SEQUENCED_AT.value,
            METADATA_FIELD_VALUE: sample.last_sequenced_at,
        },
        {
            METADATA_FIELD_NAME: MetadataFields.TICKET_NUMBER.value,
            METADATA_FIELD_VALUE: sample.original_ticket,
        },
    ]
    return metadata
