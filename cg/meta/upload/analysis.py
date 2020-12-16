"""Api to upload analysis results to Housekeeper"""
import logging
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper import models as hk_models
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import AnalysisUploadError

LOG = logging.getLogger(__name__)


class UploadAnalysisApi:
    def __init__(self, hk_api: HousekeeperAPI, hermes_api: HermesApi):
        LOG.info("Initialising UploadAnalysisApi")
        self.hk_api = hk_api
        self.hermes_api = hermes_api

    def upload_deliverables(
        self, deliverables_file: Path, pipeline: str, analysis_type: Optional[str] = None
    ) -> None:
        """Convert and validate deliverables with hermes and upload them to housekeeper

        Hermes will convert the deliverables to a format that CG knows, this will then be converted to a housekeeper
        bundle and loaded into housekeeper.
        """
        try:
            cg_deliverables: CGDeliverables = self.hermes_api.convert_deliverables(
                deliverables_file=deliverables_file, pipeline=pipeline, analysis_type=analysis_type
            )
        except CalledProcessError as err:
            LOG.warning("Something went wrong when validating the deliverables file")
            LOG.info(err)
            raise AnalysisUploadError("Could not store deliverables")
        housekeeper_bundle: hk_models.InputBundle = self.create_housekeeper_bundle(cg_deliverables)
        LOG.info("Uploading analysis results from %s to housekeeper", deliverables_file)
        self.hk_api.add_bundle(housekeeper_bundle.dict())

    @staticmethod
    def create_housekeeper_bundle(deliverables: CGDeliverables) -> hk_models.InputBundle:
        """Convert a deliverables object to a housekeeper object"""
        bundle_info = {
            "name": deliverables.bundle_id,
            "files": [file_info.dict() for file_info in deliverables.files],
        }
        bundle = hk_models.InputBundle(**bundle_info)
        return bundle

    def __str__(self):
        return "UploadAnalysisApi()"


if __name__ == "__main__":
    deliverables_info = {
        "bundle_id": "201116_hej",
        "files": [
            {
                "path": "/castor/project/proj_nobackup/wharf/jesperei/jesperei-sens2019010/fluffy_header/fluffy/201116_hej/summary.csv",
                "tags": ["metrics", "201116_hej", "nipt"],
            },
            {
                "path": "/castor/project/proj_nobackup/wharf/jesperei/jesperei-sens2019010/fluffy_header/fluffy/201116_hej/multiqc_report.html",
                "tags": ["multiqc-html", "201116_hej", "nipt"],
            },
            {
                "path": "/castor/project/proj_nobackup/wharf/jesperei/jesperei-sens2019010/fluffy_header/fluffy/201116_hej/2020-23219-05/2020-23219-05.WCXpredict_aberrations.filt.bed",
                "tags": ["wisecondor", "cnv", "2020-23219-05", "nipt"],
            },
            {
                "path": "/castor/project/proj_nobackup/wharf/jesperei/jesperei-sens2019010/fluffy_header/fluffy/201116_hej/2020-23220-05/2020-23220-05.WCXpredict_aberrations.filt.bed",
                "tags": ["wisecondor", "cnv", "2020-23220-05", "nipt"],
            },
        ],
        "pipeline": "fluffy",
    }
    deliverables_obj = CGDeliverables(**deliverables_info)
    hk_bundle = UploadAnalysisApi.create_housekeeper_bundle(deliverables_obj)
    print(hk_bundle.dict())
