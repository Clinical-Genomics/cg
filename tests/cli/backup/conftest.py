import pytest

from cg.services.illumina.backup.backup_service import IlluminaBackupService
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store


@pytest.fixture
def backup_context(cg_context: CGConfig, store_with_illumina_sequencing_data: Store) -> CGConfig:
    cg_context.meta_apis["backup_api"] = IlluminaBackupService(
        encryption_api=EncryptionAPI(binary_path=cg_context.encryption.binary_path),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status_db=store_with_illumina_sequencing_data,
        tar_api=TarAPI(binary_path=cg_context.tar.binary_path),
        pdc_service=cg_context.pdc_service,
        sequencing_runs_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )
    cg_context.status_db_ = store_with_illumina_sequencing_data
    return cg_context
