""" Module for retrieving FCs from backup """
import logging
import subprocess
import time
from typing import Optional

from cg.apps.pdc import PdcApi
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class BackupApi:
    """Class for retrieving FCs from backup"""

    def __init__(self, status: Store, pdc_api: PdcApi, max_flowcells_on_disk: int, root_dir: dict):
        self.status: Store = status
        self.pdc: PdcApi = pdc_api
        self.max_flowcells_on_disk: int = max_flowcells_on_disk
        self.root_dir: dict = root_dir

    def maximum_flowcells_ondisk(self) -> bool:
        """Check if there's too many flowcells already "ondisk"."""
        ondisk_flowcells = self.status.flowcells(status="ondisk").count()
        LOG.debug("ondisk flowcells: %s", ondisk_flowcells)
        return ondisk_flowcells > self.max_flowcells_on_disk

    def check_processing(self, max_processing_flowcells: int = 1) -> bool:
        """Check if the processing queue for flowcells is not full."""
        processing_flowcells = self.status.flowcells(status="processing").count()
        LOG.debug("processing flowcells: %s", processing_flowcells)
        return processing_flowcells < max_processing_flowcells

    def pop_flowcell(self, dry_run: bool) -> Optional[models.Flowcell]:
        """
        Get the top flowcell from the requested queue and update status to
        "processing".
        """
        flowcell_obj: Optional[models.Flowcell] = self.status.flowcells(status="requested").first()
        if not flowcell_obj:
            return None

        return flowcell_obj

    def fetch_flowcell(
        self, flowcell_obj: Optional[models.Flowcell] = None, dry_run: bool = False
    ) -> Optional[float]:
        """Start fetching a flowcell from backup if possible.

        1. The processing queue is not full
        2. The requested queue is not emtpy
        """
        if self.check_processing() is False:
            LOG.info("processing queue is full")
            return None

        if self.maximum_flowcells_ondisk() is True:
            LOG.info("maximum flowcells ondisk reached")
            return None

        if not flowcell_obj:
            flowcell_obj = self.pop_flowcell(dry_run)

        if not flowcell_obj:
            LOG.info("no flowcells requested")
            return None

        flowcell_obj.status = "processing"
        if not dry_run:
            self.status.commit()
            LOG.info("%s: retrieving from PDC", flowcell_obj.name)

        start_time = time.time()

        try:
            self.pdc.retrieve_flowcell(
                flowcell_id=flowcell_obj.name,
                sequencer_type=flowcell_obj.sequencer_type,
                root_dir=self.root_dir,
                dry=dry_run,
            )
            if not dry_run:
                flowcell_obj.status = "retrieved"
                self.status.commit()
                LOG.info('Status for flowcell %s set to "retrieved"', flowcell_obj.name)
        except subprocess.CalledProcessError as error:
            LOG.error("%s: retrieval failed", flowcell_obj.name)
            if not dry_run:
                flowcell_obj.status = "requested"
                self.status.commit()
            raise error

        end_time = time.time()
        return end_time - start_time
