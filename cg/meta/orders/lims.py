import logging
from typing import List

from cg.apps.lims import LimsAPI
from cg.models.lims.sample import LimsSample, Udf

LOG = logging.getLogger(__name__)


def to_lims(customer: str, samples: List[dict]) -> List[LimsSample]:
    """Convert order input to lims interface input."""
    samples_lims = []
    for sample in samples:
        LOG.debug(f"{sample['name']}: prepare LIMS input")
        sample["customer"] = customer
        lims_sample: LimsSample = LimsSample.parse_obj(sample)
        udf: Udf = Udf.parse_obj(sample)
        lims_sample.udfs = udf
        samples_lims.append(lims_sample)
    return samples_lims


def process_lims(lims_api: LimsAPI, data: dict, samples: List[dict]):
    """Process samples to add them to LIMS."""
    samples_lims: List[LimsSample] = to_lims(data["customer"], samples)
    project_name = data["ticket"] or data["name"]
    # Create new lims project
    project_data = lims_api.submit_project(
        project_name, [lims_sample.dict() for lims_sample in samples_lims]
    )
    lims_map = lims_api.get_samples(projectlimsid=project_data["id"], map_ids=True)
    return project_data, lims_map
