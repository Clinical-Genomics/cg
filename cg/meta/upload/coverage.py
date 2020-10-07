"""Upload coverage API"""
import logging

from cg.apps.hk import HousekeeperAPI
from cg.apps.coverage import ChanjoAPI
from cg.store import models, Store

LOG = logging.getLogger(__name__)


class UploadCoverageApi:
    """Upload coverage API"""

    def __init__(self, status_api: Store, hk_api: HousekeeperAPI, chanjo_api: ChanjoAPI):
        self.status_api = status_api
        self.hk_api = hk_api
        self.chanjo_api = chanjo_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Get data for uploading coverage."""
        family_id = analysis_obj.family.internal_id
        data = {"family": family_id, "family_name": analysis_obj.family.name, "samples": []}
        for link_obj in analysis_obj.family.links:
            analysis_date = analysis_obj.started_at or analysis_obj.completed_at
            hk_version = self.hk_api.version(family_id, analysis_date)
            hk_coverage = self.hk_api.files(
                version=hk_version.id, tags=[link_obj.sample.internal_id, "coverage"]
            ).first()
            data["samples"].append(
                {
                    "sample": link_obj.sample.internal_id,
                    "sample_name": link_obj.sample.name,
                    "coverage": hk_coverage.full_path,
                }
            )
        return data

    def upload(self, data: dict, replace: bool = False):
        """Upload coverage to Chanjo from an analysis."""
        for sample_data in data["samples"]:
            chanjo_sample = self.chanjo_api.sample(sample_data["sample"])
            if chanjo_sample and replace:
                self.chanjo_api.delete_sample(sample_data["sample"])
            elif chanjo_sample:
                LOG.warning("sample already loaded, skipping: %s", sample_data["sample"])
                continue

            LOG.debug("upload coverage for sample: %s", sample_data["sample"])
            self.chanjo_api.upload(
                sample_id=sample_data["sample"],
                sample_name=sample_data["sample_name"],
                group_id=data["family"],
                group_name=data["family_name"],
                bed_file=sample_data["coverage"],
            )
