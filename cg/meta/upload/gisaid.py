import logging
from pathlib import Path
from typing import List

from cg.apps.gisaid.gisaid import GisaidAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.hk import models as housekeeper_models
from cg.store import models

LOG = logging.getLogger(__name__)


class UploadGisaidAPI(object):
    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gisaid_api: GisaidAPI,
        samples: List[models.Sample],
        family_id: str,
    ):
        LOG.info("Initializing UploadGisaidAPI")
        self.hk = hk_api
        self.gisaid_api = gisaid_api
        self.samples = samples
        self.family_id = family_id

    def files(self) -> dict:
        """Fetch csv file and fasta file for batch upload to GISAID."""

        return dict(
            csv_file=self.get_csv_file(),
            fasta_file="file_path",  # self.get_fasta_file(hk_version_obj=self.hk),
        )

    def get_csv_file(self) -> Path:
        """Generates csv file for batch upload to gisaid."""

        csv_file = self.gisaid_api.build_batch_csv(samples=self.samples, family_id=self.family_id)
        return csv_file

    def get_fasta_file(self, hk_version_obj: housekeeper_models.Version) -> Path:
        """Fetch a fasta file form house keeper for batch upload to gisaid"""

        hk_mututnt_fasta = self.hk.files(version=hk_version_obj.id, tags=["consensus"]).first()
        LOG.debug("Found  metrics file %s", hk_mututnt_fasta.full_path)
        return Path(hk_mututnt_fasta.full_path)

    def upload(self, csv_file: str, fasta_file: str):
        """Upload data about genotypes for a family of samples."""
        self.gisaid_api.upload(csv_file_path=csv_file, fasta_file_path=fasta_file)
