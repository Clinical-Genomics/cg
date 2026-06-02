"""Abstract base classes for order submitters."""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar

from genologics.entities import Sample as LimsSample
from genologics.lims import Artifact
from requests import HTTPError

from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)

SampleType = TypeVar("SampleType", bound=Sample)


class StoreOrderService(ABC):
    @abstractmethod
    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    @abstractmethod
    def store_order(self, order: Order):
        pass

    @staticmethod
    def _fill_in_sample_ids(samples: list[SampleType], lims_map: dict) -> None:
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample.name}: link sample to LIMS")
            internal_id = lims_map[sample.name]
            LOG.info(f"{sample.name} -> {internal_id}: connect sample to LIMS")
            sample._generated_lims_id = internal_id

    def _queue_samples_in_workflow(self, samples: list[SampleType]) -> None:
        """Given a list of order samples, this method will

        for each sample:
        - Find a unique matching LIMS sample by matching ID (relies on ´_fill_in_sample_ids´)
        - Collect the appropriate LIMS workflow ID via the Application database table

        for each collected workflow ID:
        - Attempt to route all sample artifacts destined for that workflow via the LIMS API
        """
        # Build dict mapping workflow ID to a list of LIMS artifacts to be routed
        wf_id2arts: dict[str, list[Artifact]] = {}
        for sample in samples:
            lims_sample = LimsSample(self.lims.lims_api, id=sample._generated_lims_id)
            lims_art: Artifact = lims_sample.artifact  # type: ignore

            wf_id = self.status_db.get_lims_workflow_id_by_application_tag(sample.application)
            if not wf_id:
                LOG.info(
                    f"Sample {lims_sample.id} has no LIMS workflow ID associated to it's application, skipping."
                )
                continue

            if wf_id not in wf_id2arts:
                wf_id2arts[wf_id] = [lims_art]  # type: ignore
            else:
                wf_id2arts[wf_id].append(lims_art)

        for wf_id, arts in wf_id2arts.items():
            LOG.info(f"Routing artifacts {[art.name for art in arts]} to workflow {wf_id}.")
            try:
                self.lims.lims_api.route_artifacts(
                    artifact_list=arts,
                    workflow_uri=f"{self.lims.lims_api.get_uri()}/configuration/workflows/{wf_id}",
                )
            except HTTPError:
                LOG.exception(f"Failed to add {len(arts)} artifacts to workflow {wf_id}.")
                continue
