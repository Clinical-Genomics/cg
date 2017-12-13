from cg.apps.pdc import PdcApi
from cg.store import Store, models


class BackupApi():

    def __init__(self, status: Store, pdc_api: PdcApi):
        self.status = status
        self.pdc = pdc_api

    def check_processing(self, max: int=3) -> bool:
        """Check if the processing queue for flowcells is not full."""
        pass

    def pop_flowcell(self) -> models.Flowcell:
        """
        Get the top flowcell from the requested queue and update status to
        "processing".
        """
        pass
    
    def fetch_flowcell(self):
        """Start fetching a flowcell from backup if possible.
        
        1. The processing queue is not full
        2. The requested queue is not emtpy
        """
        pass
