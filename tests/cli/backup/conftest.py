import pytest

from cg.meta.backup.backup import BackupApi
from cg.meta.backup.pdc import PdcAPI
from cg.models.cg_config import CGConfig


@pytest.fixture(name="backup_context")
def fixture_backup_context(cg_context: CGConfig) -> CGConfig:
    cg_context.meta_apis["backup_api"] = BackupApi(
        status=cg_context.status_db,
        pdc_api=PdcAPI(),
        root_dir=cg_context.backup.root.dict(),
    )
    return cg_context
