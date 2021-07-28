"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import logging
from pathlib import Path

from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.hasta_path: Path = Path(config.external.hasta)
        self.caesar_path: Path = Path(config.external.caesar)

    def download_from_caesar(self, ticket_id: int, dry_run: bool):
        print("hej")
