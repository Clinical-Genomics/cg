"""Abstract base classes for order submitters."""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar

from genologics.entities import Sample as LimsSample
from requests import HTTPError

from cg.exc import LimsWorkflowRoutingError, MissingLimsUdfError
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)

SampleType = TypeVar("SampleType", bound=Sample)

APPTAG_UDF_NAME = "Sequencing Analysis"


class StoreOrderService(ABC):
    @abstractmethod
    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    @abstractmethod
    def store_order(self, order: Order):
        pass

    @staticmethod
    def _fill_in_sample_ids(samples: list[SampleType], lims_samples: list[LimsSample]) -> None:
        """Fill in LIMS sample ids."""
        name2id = {s.name: s.id for s in lims_samples}
        for sample in samples:
            LOG.info(f"{sample.name} -> {name2id[sample.name]}: connect sample to LIMS")
            sample._generated_lims_id = name2id[sample.name]  # type: ignore

    def _queue_samples_in_workflow(self, lims_samples: list[LimsSample]) -> None:
        f"""Given a list of LIMS sample objects, this method will

        for each sample:
        - Get the apptag from the LIMS sample UDF '{APPTAG_UDF_NAME}'
        - Use the apptag to get the corresponding LIMS workflow ID via the Application database table

        for each collected workflow ID:
        - Collect each associated sample
        - Attempt to route all sample artifacts to the workflow via the LIMS API
        """
        # Build dict mapping each workflow ID to a list of LIMS samples to be routed
        wf_id2samples: dict[int, list[LimsSample]] = {}
        for lims_sample in lims_samples:
            try:
                apptag = lims_sample.udf[APPTAG_UDF_NAME]
            except KeyError:
                raise MissingLimsUdfError(
                    f"Sample {lims_sample.id} has no UDF '{APPTAG_UDF_NAME}'."
                )
            wf_id: int | None = self.status_db.get_lims_workflow_id_by_application_tag(apptag)
            if not wf_id:
                LOG.info(
                    f"Sample {lims_sample.id} has no LIMS workflow ID associated to it's apptag '{apptag}', skipping."
                )
                continue

            if wf_id not in wf_id2samples:
                wf_id2samples[wf_id] = [lims_sample]  # type: ignore
            else:
                wf_id2samples[wf_id].append(lims_sample)  # type: ignore

        for wf_id, samples in wf_id2samples.items():
            LOG.info(f"Routing samples {[sample.id for sample in samples]} to workflow {wf_id}.")
            try:
                self.lims.lims_api.route_artifacts(
                    artifact_list=[sample.artifact for sample in samples],  # type: ignore
                    workflow_uri=f"{self.lims.lims_api.get_uri()}/configuration/workflows/{wf_id}",
                )
            except HTTPError:
                raise LimsWorkflowRoutingError(
                    f"Failed to route samples {[sample.id for sample in samples]} to workflow {wf_id}."
                )
