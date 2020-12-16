"""Api to upload analysis results to Housekeeper"""
from pathlib import Path

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI


class UploadAnalysisApi:
    def __init__(self, hk_api: HousekeeperAPI, hermes_api: HermesApi):
        self.hk_api = hk_api
        self.hermes_api = hermes_api

    def upload_deliverables(self, deliverables_file: Path):
        """Convert and validate deliverables with hermes and upload them to housekeeper

        Hermes will convert the deliverables to a format that CG knows, this will then be converted to a housekeeper
        bundle and loaded into housekeeper.
        """
        cg_deliverables: CGDeliverables = self.hermes_api.convert_deliverables(
            deliverables_file=deliverables_file
        )

    def create_housekeeper_bundle(self):

