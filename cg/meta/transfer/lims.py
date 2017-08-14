# -*- coding: utf-8 -*-
import logging

from cg.store import Store
from cg.apps.lims import LimsAPI

log = logging.getLogger(__name__)


class TransferLims(object):

    def __init__(self, db: Store, lims: LimsAPI):
        self.db = db
        self.lims = lims

    def transfer_samples(self, status):
        """Transfer information about samples."""
        samples = (self.db.samples_to_recieve() if status == 'received' else
                   self.db.samples_to_deliver())
        for sample_obj in samples:
            status_date = (self.lims.get_received_date(sample_obj.internal_id)
                           if status == 'received' else
                           self.lims.get_delivery_date(sample_obj.internal_id))
            if status_date is None:
                log.debug(f"no {status} date found for {sample_obj.internal_id}")
            else:
                log.info(f"found {status} date for {sample_obj.internal_id}: {status_date}")
                setattr(sample_obj, f"{status}_at", status_date)
                self.db.commit()
