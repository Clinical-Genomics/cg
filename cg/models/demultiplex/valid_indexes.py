import logging

from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class Index(BaseModel):
    name: str
    sequence: str
