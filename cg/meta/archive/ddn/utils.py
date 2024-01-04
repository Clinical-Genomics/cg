from cg.meta.archive.ddn.constants import MetadataFields
from cg.store.models import Sample


def get_metadata(sample: Sample) -> list[dict]:
    """Returns metadata generated from a sample."""
    metadata: list[dict] = [
        {"metadataName": MetadataFields.CUSTOMER_NAME.value, "value": sample.customer.name},
        {"metadataName": MetadataFields.PREP_CATEGORY.value, "value": sample.prep_category},
        {"metadataName": MetadataFields.SAMPLE_NAME.value, "value": sample.name},
        {"metadataName": MetadataFields.SEQUENCED_AT.value, "value": sample.last_sequenced_at},
        {"metadataName": MetadataFields.TICKET_NUMBER.value, "value": sample.original_ticket},
    ]
    return metadata
