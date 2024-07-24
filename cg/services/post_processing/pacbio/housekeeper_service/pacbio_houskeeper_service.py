"""Module for the PacBioHousekeeperService used in the Post processing flow."""

from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.post_processing.abstract_classes import PostProcessingHKService


class PacBioHousekeeperService(PostProcessingHKService):

    def __init__(self, hk_api: HousekeeperAPI, file_manager: PacBioFileManager):
        super().__init__(hk_api=hk_api, file_manager=file_manager)

    def store_files_in_housekeeper(self):
        pass
