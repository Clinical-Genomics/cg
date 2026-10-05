from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.services.events.constants import SAMPLE_INTERNAL_ID_FIELD
from cg.services.events.event_metadata import EventMetadata
from cg.store.models import Sample


def handle(config: CGConfig, event_payload: dict, event_metadata: EventMetadata):
    sample: Sample = config.status_db.get_sample_by_internal_id_strict(
        internal_id=event_payload[SAMPLE_INTERNAL_ID_FIELD]
    )
    transfer_to_cluster_service.transfer_sample(cg_config=config, sample=sample)
