# -*- coding: utf-8 -*-
import logging

from cg.store import Store
from cg.apps.lims import LimsAPI

LOG = logging.getLogger(__name__)


class TransferLims(object):

    def __init__(self, status: Store, lims: LimsAPI):
        self.status = status
        self.lims = lims

    def transfer_samples(self, status_type: str):
        """Transfer information about samples."""
        samples = (self.status.samples_to_recieve() if status_type == 'received' else
                   self.status.samples_to_deliver())
        for sample_obj in samples:
            status_date = (self.lims.get_received_date(sample_obj.internal_id)
                           if status_type == 'received' else
                           self.lims.get_delivery_date(sample_obj.internal_id))
            if status_date is None:
                LOG.debug(f"no {status_type} date found for {sample_obj.internal_id}")
            else:
                LOG.info(f"found {status_type} date for {sample_obj.internal_id}: {status_date}")
                setattr(sample_obj, f"{status_type}_at", status_date)
                self.status.commit()
