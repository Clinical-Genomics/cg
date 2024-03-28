"""Delivery API related models."""

from pathlib import Path

from pydantic import BaseModel, FilePath


class DeliveryFile(BaseModel):
    """Model representing a file to be delivered."""

    source_path: FilePath
    destination_path: Path
