import logging
from enum import Enum
from typing import Dict, Union, List

from cg.store.models import Pool, Sample
import genologics.entities
from cg.apps.lims import LimsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class SampleState(Enum):
    RECEIVED = "received"
    PREPARED = "prepared"
    DELIVERED = "delivered"


class PoolState(Enum):
    RECEIVED = "received"
    DELIVERED = "delivered"


class IncludeOptions(Enum):
    UNSET = "unset"
    NOTINVOICED = "not-invoiced"
    ALL = "all"


class TransferLims(object):
    def __init__(self, status: Store, lims: LimsAPI):
        self.status = status
        self.lims = lims

        self._sample_functions = {
            SampleState.RECEIVED: self.status.get_samples_to_receive,
            SampleState.PREPARED: self.status.get_samples_to_prepare,
            SampleState.DELIVERED: self.status.get_samples_to_deliver,
        }

        self._pool_functions = {
            PoolState.RECEIVED: self.status.get_pools_to_receive,
            PoolState.DELIVERED: self.status.get_all_pools_to_deliver,
        }

        self._date_functions = {
            SampleState.RECEIVED: self.lims.get_received_date,
            SampleState.PREPARED: self.lims.get_prepared_date,
            SampleState.DELIVERED: self.lims.get_delivery_date,
            PoolState.RECEIVED: self.lims.get_received_date,
            PoolState.DELIVERED: self.lims.get_delivery_date,
        }

    def transfer_samples(
        self, status_type: SampleState, include: str = "unset", sample_id: str = None
    ):
        """Transfer information about samples."""

        if sample_id:
            samples: List[Sample] = self.status.get_samples_by_internal_id(internal_id=sample_id)
        else:
            samples: List[Sample] = self._get_samples_to_include(include, status_type)

        if samples is None:
            LOG.info(f"No samples to process found with {include} {status_type.value}")
            return
        else:
            LOG.info(f"{len(samples)} samples to process")

        for sample_obj in samples:
            lims_date = self._date_functions[status_type](sample_obj.internal_id)
            statusdb_date = getattr(sample_obj, f"{status_type.value}_at")
            if lims_date:
                if statusdb_date and statusdb_date.date() == lims_date:
                    continue

                LOG.info(
                    f"Found new {status_type.value} date for {sample_obj.internal_id}: "
                    f"{lims_date}, old value: {statusdb_date} "
                )

                setattr(sample_obj, f"{status_type.value}_at", lims_date)
                self.status.session.commit()
            else:
                LOG.debug(f"no {status_type.value} date found for {sample_obj.internal_id}")

    def _get_samples_to_include(self, include, status_type):
        samples = None
        if include == IncludeOptions.UNSET.value:
            samples = self._get_samples_in_step(status_type)
        elif include == IncludeOptions.NOTINVOICED.value:
            samples = self.status.get_samples_not_invoiced()
        elif include == IncludeOptions.ALL.value:
            samples = self.status.get_samples_not_down_sampled()
        return samples

    def transfer_pools(self, status_type: PoolState):
        """Transfer information about pools."""
        pools = self._pool_functions[status_type]()

        for pool_obj in pools:
            ticket: str = pool_obj.ticket
            number_of_samples: int = self.lims.get_sample_number(projectname=ticket)
            if not self._is_pool_valid(pool_obj, ticket, number_of_samples):
                continue

            samples_in_pool: Union[Dict[str:str], List[genologics.Sample]] = self.lims.get_samples(
                projectname=ticket
            )
            for sample_obj in samples_in_pool:
                if not self._is_sample_valid(pool_obj, sample_obj):
                    continue
                status_date = self._date_functions[status_type](sample_obj.id)
                if status_date is None:
                    continue

                LOG.info(
                    "Found %s date for pool id %s: %s",
                    status_type.value,
                    pool_obj.id,
                    status_date,
                )
                setattr(pool_obj, f"{status_type.value}_at", status_date)
                self.status.session.commit()
                break

    def _get_samples_in_step(self, status_type) -> List[Sample]:
        return self._sample_functions[status_type]()

    @staticmethod
    def _is_pool_valid(pool_obj: Pool, ticket: str, number_of_samples: int) -> bool:
        """Checks if a pool object can be transferred. A pool needs to have a ticket number and at least one sample"""

        if ticket is None:
            LOG.warning(f"No ticket number found for pool with order number {pool_obj.order}.")
            return False
        if number_of_samples == 0:
            LOG.warning(f"No samples found for pool with ticket number {ticket}.")
            return False
        return True

    @staticmethod
    def _is_sample_valid(pool_obj: Pool, sample_obj: genologics.entities.Sample) -> bool:
        """Checks if a sample can have the status date set. A sample needs to have a udf "pool name" that matches the
        name of the pool object it's part of"""
        if sample_obj.udf.get("pool name") is None:
            LOG.warning(
                "No pool name found for sample %s (sample name %s, project %s)",
                sample_obj.id,
                sample_obj.name,
                sample_obj.project.name,
            )
            return False

        sample_pool_name = sample_obj.udf["pool name"]
        if sample_pool_name != pool_obj.name:
            LOG.warning(
                "The udf 'pool name' of the sample (%s) does not match the name of the pool (%s))",
                sample_pool_name,
                pool_obj.name,
            )
            return False
        return True
