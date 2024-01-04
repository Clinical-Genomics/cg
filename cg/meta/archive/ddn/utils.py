from cg.meta.archive.ddn.constants import MetadataFields
from cg.store.models import Sample


def get_metadata(sample: Sample) -> list[dict]:
    """Returns metadata generated from a sample."""
    metadata: list[dict] = []
    metadata.append({MetadataFields.CUSTOMER_NAME: sample.customer.name})
    metadata.append({MetadataFields.PREP_CATEGORY: sample.prep_category})
    metadata.append({MetadataFields.SAMPLE_NAME: sample.name})
    metadata.append({MetadataFields.SEQUENCED_AT: sample.last_sequenced_at})
    metadata.append({MetadataFields.TICKET_NUMBER: sample.original_ticket})
    return metadata
