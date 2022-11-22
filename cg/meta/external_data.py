import logging
from pathlib import Path

from housekeeper.store import models as hk_models
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import HK_FASTQ_TAGS
from cg.constants.constants import CaseActions
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class ExternalDataHandler:
    """Class for handling the integration of external data into the common workflow."""

    def __init__(self, config: CGConfig):
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.external_data_dir = Path(config.external.external_data_dir)

    def curate_external_folder(self):
        """Iterates through the external data directory and creates/updates housekeeper when new
        files are added."""
        for customer_folder in self.external_data_dir.iterdir():
            customer: models.Customer = self.status_db.customer(customer_folder.name)
            for sample_folder in customer_folder.iterdir():
                sample_object: models.Sample = self.status_db.find_samples(
                    customer=customer, name=sample_folder.name
                ).first()
                self.add_sample_to_hk(sample_folder=sample_folder, sample_object=sample_object)

    def add_sample_to_hk(self, sample_folder: Path, sample_object: models.Sample):
        """Creates a housekeeper bundle for a sample if non-existant and adds any file that is
        not already added."""
        hk_version: hk_models.Version = self.hk_api.get_create_version(
            bundle=sample_object.internal_id
        )
        for fastq_file in sample_folder.iterdir():
            if self.hk_api.files(version=hk_version, path=fastq_file.as_posix()):
                LOG.debug(f"File {fastq_file} already added to bundle {hk_version.bundle.name}")
                continue
            LOG.info(f"File {fastq_file} added to bundle {hk_version.bundle.name}")
            self.hk_api.add_file(path=fastq_file, tags=HK_FASTQ_TAGS, version_obj=hk_version)
        self.hk_api.commit()
        self.start_associated_case(sample_object=sample_object)

    def start_associated_case(self, sample_object: models.Sample):
        """Sets the action to analyze for any case linked to the sample."""
        for case_link in sample_object.links:
            self.status_db.set_case_action(
                action=CaseActions.ANALYZE, case_id=case_link.family.internal_id
            )
