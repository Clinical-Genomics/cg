import logging
import subprocess
import time

from cg.apps.pdc import PdcApi
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class BackupApi():

    def __init__(self, status: Store, pdc_api: PdcApi):
        self.status = status
        self.pdc = pdc_api

    def maximum_flowcells_ondisk(self, max_flowcells: int=700) -> bool:
        """Check if there's too many flowcells already "ondisk"."""
        ondisk_flowcells = self.status.flowcells(status='ondisk').count()
        LOG.debug(f"ondisk flowcells: {ondisk_flowcells}")
        return ondisk_flowcells > max_flowcells

    def check_processing(self, max_flowcells: int=3) -> bool:
        """Check if the processing queue for flowcells is not full."""
        processing_flowcells = self.status.flowcells(status='processing').count()
        LOG.debug(f"processing flowcells: {processing_flowcells}")
        return processing_flowcells < max_flowcells

    def pop_flowcell(self) -> models.Flowcell:
        """
        Get the top flowcell from the requested queue and update status to
        "processing".
        """
        flowcell_obj = self.status.flowcells(status='requested').first()
        if flowcell_obj is not None:
            flowcell_obj.status = 'processing'
            self.status.commit()
        return flowcell_obj

    def fetch_flowcell(self, flowcell_obj: models.Flowcell=None):
        """Start fetching a flowcell from backup if possible.

        1. The processing queue is not full
        2. The requested queue is not emtpy
        """
        if self.check_processing() is False:
            LOG.info('processing queue is full')
            return None

        if self.maximum_flowcells_ondisk() is True:
            LOG.info('maximum flowcells ondisk reached')
            return None

        if flowcell_obj is None:
            flowcell_obj = self.pop_flowcell()
            if flowcell_obj is None:
                LOG.info('no flowcells requested')
                return None

        LOG.info(f"{flowcell_obj.name}: retreiving from PDC")
        tic = time.time()
        try:
            self.pdc.retrieve_flowcell(flowcell_obj.name, flowcell_obj.sequencer_type)
        except subprocess.CalledProcessError as error:
            LOG.error(f"{flowcell_obj.name}: retrieval failed")
            flowcell_obj.status = 'requested'
            self.status.commit()
            raise error
        toc = time.time()
        return toc - tic
