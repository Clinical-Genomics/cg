import pytest

from cg.meta.backup.backup import BackupApi
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig


@pytest.fixture(name="backup_context")
def fixture_backup_context(cg_context: CGConfig) -> CGConfig:
    cg_context.meta_apis["backup_api"] = BackupApi(
        encryption_api=EncryptionAPI(binary_path=cg_context.encryption.binary_path),
        status=cg_context.status_db,
        tar_api=TarAPI(binary_path=cg_context.tar.binary_path),
        pdc_api=PdcAPI(binary_path=cg_context.pdc.binary_path),
        root_dir=cg_context.backup.root.dict(),
    )
    return cg_context
