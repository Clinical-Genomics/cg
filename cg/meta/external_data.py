import datetime
import datetime as dt
import logging
from pathlib import Path

from housekeeper.store.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import HK_FASTQ_TAGS
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample, Customer
from cg.utils.time import get_file_timestamp

LOG = logging.getLogger(__name__)


class ExternalDataHandler:
    """Class for handling the integration of external data into the common workflow."""

    def __init__(self, config: CGConfig):
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.external_data_dir: Path = Path(config.external.external_data_dir)

    def curate_external_folder(self):
        """Iterates through the external data directory and creates/updates housekeeper when new
        files are added."""
        for customer_folder in self.external_data_dir.iterdir():
            customer: Customer = self.status_db.customer(customer_folder.name)
            for sample_folder in customer_folder.iterdir():
                sample: Sample = self.status_db.find_samples(
                    customer=customer, name=sample_folder.name
                ).first()
                if self.is_recent_file_system_entry(file_system_entry=sample_folder):
                    LOG.info(f"Folder {sample_folder} has recent changes. Skipping")
                    continue
                if sample:
                    new_folder: Path = sample_folder.parent.joinpath(sample.internal_id)
                    sample_folder.rename(new_folder)
                    self.add_sample_to_hk(sample_folder=new_folder, sample=sample)
                    continue
                if self.status_db.sample(internal_id=sample_folder.name):
                    LOG.debug(
                        f"Sample {sample.internal_id} has already been added to Housekeeper. "
                        f"Skipping"
                    )
                    continue
                LOG.warning(
                    f"No sample with the name {sample.name} exists for {customer.internal_id} "
                    f"in status-db. Make sure an order has been placed and "
                    f"the sample/folder has been named correctly"
                )

    def add_sample_to_hk(self, sample_folder: Path, sample: Sample):
        """Creates a housekeeper bundle for a sample if non-existant and adds any file that is
        not already added."""
        hk_version: Version = self.hk_api.get_create_version(bundle=sample.internal_id)
        for fastq_file in sample_folder.iterdir():
            if self.hk_api.files(version=hk_version, path=fastq_file.as_posix()):
                LOG.debug(f"File {fastq_file} already added to bundle {hk_version.bundle.name}")
                continue
            self.hk_api.add_file(path=fastq_file, tags=HK_FASTQ_TAGS, version_obj=hk_version)
            LOG.info(f"File {fastq_file} added to bundle {hk_version.bundle.name}")
        sample.sequenced_at = datetime.datetime.now()
        self.status_db.commit()
        self.hk_api.commit()

    @staticmethod
    def is_recent_file_system_entry(file_system_entry: Path) -> bool:
        """Checks if a file or directory has changed recently."""
        return dt.datetime.now() - get_file_timestamp(file_system_entry) < dt.timedelta(hours=4)
