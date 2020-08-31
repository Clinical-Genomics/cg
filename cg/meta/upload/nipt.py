"""API to run nipt"""

import json

from cg.apps.nipt import NiptAPI
from cg.apps.hk import HousekeeperAPI


class UploadNiptAPI:
    """API to load data into nipt"""

    def __init__(self, nipt_api: NiptAPI, hk_api: HousekeeperAPI):
        self.nipt_api = nipt_api
        self.housekeeper = hk_api


    def load_batches(self) -> None:
        """Running nipt load batch."""

        ## get latest files eller vad är planen?
        files = self.housekeeper.files(version=???, tags=["nipt????"])
        
        for batch_file in files:
            batch_dict = json.loads(batch_file.full_path)
            self.nipt_api.load_batch(batch_dict)
