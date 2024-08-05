"""Upload coverage API"""

import logging

from cg.apps.coverage import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store.models import Analysis
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class UploadCoverageApi:
    """Upload coverage API"""

    def __init__(self, status_api: Store, hk_api: HousekeeperAPI, chanjo_api: ChanjoAPI):
        self.status_api = status_api
        self.hk_api = hk_api
        self.chanjo_api = chanjo_api

    def data(self, analysis_obj: Analysis) -> dict:
        """Get data for uploading coverage."""
        family_id = analysis_obj.case.internal_id
        data = {"family": family_id, "family_name": analysis_obj.case.name, "samples": []}
        for link_obj in analysis_obj.case.links:
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

    def upload(self, data: dict):
        """
        Upload coverage to Chanjo from an analysis.
        If a previous coverage exists for a sample, it will be deleted before re-uploading.
        """
        for sample_data in data["samples"]:
            chanjo_sample = self.chanjo_api.sample(sample_data["sample"])
            if chanjo_sample:
                LOG.warning(
                    f"Sample already loaded, deleting previous entry and re-uploading: {sample_data['sample']}"
                )
                self.chanjo_api.delete_sample(sample_data["sample"])

            LOG.debug(f"upload coverage for sample: {sample_data['sample']}")
            self.chanjo_api.upload(
                sample_id=sample_data["sample"],
                sample_name=sample_data["sample_name"],
                group_id=data["family"],
                group_name=data["family_name"],
                bed_file=sample_data["coverage"],
            )
