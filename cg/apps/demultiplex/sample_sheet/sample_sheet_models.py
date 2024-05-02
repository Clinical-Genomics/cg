import logging
from collections import defaultdict

from pydantic import BaseModel

from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample

LOG = logging.getLogger(__name__)


class SampleSheet(BaseModel):
    samples: list[FlowCellSample]

    def get_non_pooled_lanes_and_samples(self) -> list[tuple[int, str]]:
        """Return tuples of non-pooled lane and sample ids."""
        non_pooled_lane_sample_id_pairs: list[tuple[int, str]] = []
        non_pooled_samples: list[FlowCellSample] = self.get_non_pooled_samples()
        for sample in non_pooled_samples:
            non_pooled_lane_sample_id_pairs.append((sample.lane, sample.sample_id))
        return non_pooled_lane_sample_id_pairs

    def get_non_pooled_samples(self) -> list[FlowCellSample]:
        """Return samples that are sequenced solo in their lane."""
        lane_samples: dict[int, list[FlowCellSample]] = defaultdict(list)
        for sample in self.samples:
            lane_samples[sample.lane].append(sample)
        return [samples[0] for samples in lane_samples.values() if len(samples) == 1]

    def get_sample_ids(self) -> list[str]:
        """Return ids for samples in sheet."""
        sample_internal_ids: list[str] = []
        for sample in self.samples:
            sample_internal_ids.append(sample.sample_id)
        return list(set(sample_internal_ids))
