from pydantic import BaseModel
from datetime import datetime

# Event names
EXTERNAL_SAMPLES_ORDERED_EVENT = "external.samples_ordered"
EXTERNAL_SAMPLE_STORED_EVENT = "external.sample_storage_completed"
EXTERNAL_SAMPLE_TRANSFERRED_EVENT = "external.sample_transfer_completed"
EXTERNAL_SAMPLE_UPLOADED_EVENT = "external.sample_upload_completed"

# Payload attributes
CUSTOMER_INTERNAL_ID_FIELD = "status_db.customer.internal_id"
SAMPLE_INTERNAL_ID_FIELD = "status_db.sample.internal_id"
SAMPLE_NAME_ARRAY_FIELD = "status_db.sample.name.array"
SAMPLE_NAME_FIELD = "status_db.sample.name"


class EventSequence(BaseModel):
    consumer: int
    stream: int

class EventMetadata(BaseModel):
    # See link for more information
    # https://nats-io.github.io/nats.py/modules.html#nats.aio.msg.Msg.Metadata
    sequence: EventSequence
    num_pending: int
    num_delivered: int
    timestamp: datetime
    stream: str
    consumer: str
