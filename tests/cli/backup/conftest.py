import pytest

from cg.meta.backup.backup import BackupAPI
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig


@pytest.fixture
def backup_context(cg_context: CGConfig) -> CGConfig:
    cg_context.meta_apis["backup_api"] = BackupAPI(
        encryption_api=EncryptionAPI(binary_path=cg_context.encryption.binary_path),
        pdc_archiving_directory=cg_context.backup.pdc_archiving_directory,
        status=cg_context.status_db,
        tar_api=TarAPI(binary_path=cg_context.tar.binary_path),
        pdc_api=cg_context.pdc_api,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )
    return cg_context
