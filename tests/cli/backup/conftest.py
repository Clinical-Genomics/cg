import pytest

from cg.meta.backup.backup import BackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig


@pytest.fixture
def backup_context(cg_context: CGConfig) -> CGConfig:
    cg_context.meta_apis["backup_api"] = BackupAPI(
        encryption_api=EncryptionAPI(binary_path=cg_context.encryption.binary_path),
        encrypt_dir=cg_context.backup.encrypt_dir,
        status=cg_context.status_db,
        tar_api=TarAPI(binary_path=cg_context.tar.binary_path),
        pdc_api=PdcAPI(binary_path=cg_context.pdc.binary_path),
        flow_cells_dir=cg_context.flow_cells_dir,
    )
    return cg_context
