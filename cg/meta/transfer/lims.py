# -*- coding: utf-8 -*-
from enum import Enum
import logging

from cg.store import Store
from cg.apps.lims import LimsAPI

LOG = logging.getLogger(__name__)


class SampleState(Enum):
    RECEIVED = 'received'
    PREPARED = 'prepared'
    DELIVERED = 'delivered'


class PoolState(Enum):
    RECEIVED = 'received'
    DELIVERED = 'delivered'


class IncludeOptions(Enum):
    UNSET = 'unset'
    UNDELIVERED = 'undelivered'
    ALL = 'all'


class TransferLims(object):

    def __init__(self, status: Store, lims: LimsAPI):
        self.status = status
        self.lims = lims

        self._sample_functions = {
            SampleState.RECEIVED: self.status.samples_to_recieve,
            SampleState.PREPARED: self.status.samples_to_prepare,
            SampleState.DELIVERED: self.status.samples_to_deliver,
        }

        self._pool_functions = {
            PoolState.RECEIVED: self.status.pools_to_receive,
            PoolState.DELIVERED: self.status.pools_to_deliver,
        }

        self._date_functions = {
            SampleState.RECEIVED: self.lims.get_received_date,
            SampleState.PREPARED: self.lims.get_prepared_date,
            SampleState.DELIVERED: self.lims.get_delivery_date,
            PoolState.RECEIVED: self.lims.get_received_date,
            PoolState.DELIVERED: self.lims.get_delivery_date,
        }

    def _get_all_samples_not_yet_delivered(self):
        return self.status.samples_to_deliver()

    def transfer_samples(self, status_type: SampleState, include='unset'):
        """Transfer information about samples."""

        samples = self._get_samples_to_include(include, status_type)

        if samples is None:
            LOG.info(f"No samples to process found with {include} {status_type.value}")
            return
        else:
            LOG.info(f"{samples.count()} samples to process")

        for sample_obj in samples:
            status_date = self._date_functions[status_type](sample_obj.internal_id)

            if status_date:
                LOG.info(
                    f"found {status_type.value} date for {sample_obj.internal_id}: {status_date}")
                setattr(sample_obj, f"{status_type.value}_at", status_date)
                self.status.commit()
            else:
                LOG.debug(f"no {status_type.value} date found for {sample_obj.internal_id}")

    def _get_samples_to_include(self, include, status_type):
        samples = None
        if include == IncludeOptions.UNSET.value:
            samples = self._get_samples_in_step(status_type)
        elif include == IncludeOptions.UNDELIVERED.value:
            samples = self._get_all_samples_not_yet_delivered()
        elif include == IncludeOptions.ALL.value:
            samples = self._get_all_samples()
        return samples

    def transfer_pools(self, status_type: PoolState):
        """Transfer information about pools."""
        pools = self._pool_functions[status_type]()

        for pool_obj in pools:
            ticket_number = pool_obj.ticket_number
            number_of_samples = self.lims.get_sample_number(projectname=ticket_number)

            if ticket_number is None:
                LOG.warning(f"No ticket number found for pool with order number {pool_obj.order}.")
            elif number_of_samples == 0:
                LOG.warning(f"No samples found for pool with ticket number {ticket_number}.")
            else:
                samples_in_pool = self.lims.get_samples(projectname=ticket_number)
                for sample_obj in samples_in_pool:
                    status_date = self._date_functions[status_type](sample_obj.id)
                    if sample_obj.udf['pool name'] == pool_obj.name and status_date is not None:
                        LOG.info(f"Found {status_type.value} date for pool id {pool_obj.id}: {status_date}.")
                        setattr(pool_obj, f"{status_type.value}_at", status_date)
                        self.status.commit()
                        break
                    else:
                        continue

    def _get_all_samples(self):
        return self.status.samples()

    def _get_samples_in_step(self, status_type):
        return self._sample_functions[status_type]()
