import logging
from typing import List

from cg.apps.lims import LimsAPI
from cg.models.lims.sample import LimsSample, Udf

LOG = logging.getLogger(__name__)


def build_lims_sample(customer: str, samples: List[dict]) -> List[LimsSample]:
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


def process_lims(lims_api: LimsAPI, lims_order: dict, new_samples: List[dict]):
    """Process samples to add them to LIMS."""
    samples_lims: List[LimsSample] = build_lims_sample(lims_order["customer"], samples=new_samples)
    project_name = lims_order.get("ticket", lims_order["name"])
    # Create new lims project
    project_data = lims_api.submit_project(
        project_name, [lims_sample.dict() for lims_sample in samples_lims]
    )
    lims_map = lims_api.get_samples(projectlimsid=project_data["id"], map_ids=True)
    return project_data, lims_map
