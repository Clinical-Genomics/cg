from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.services.events.event_metadata import EventMetadata


def handle(config: CGConfig, event_payload: dict, event_metadata: EventMetadata):
    transfer_to_cluster_service.transfer_sample(cg_config=config, sample=None)
