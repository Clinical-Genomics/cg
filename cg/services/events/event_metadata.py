from datetime import datetime

from pydantic import BaseModel


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
