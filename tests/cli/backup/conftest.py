import pytest
from cg.apps.pdc import PdcApi
from cg.cli.backup import MAX_FLOWCELLS_ON_DISK
from cg.meta.backup import BackupApi
from cg.models.cg_config import CGConfig


@pytest.fixture(name="backup_context")
def fixture_backup_context(cg_context: CGConfig) -> CGConfig:
    cg_context.meta_apis["backup_api"] = BackupApi(
        status=cg_context.status_db,
        pdc_api=PdcApi(),
        max_flowcells_on_disk=cg_context.max_flowcells or MAX_FLOWCELLS_ON_DISK,
        root_dir=cg_context.backup.root.dict(),
    )
    return cg_context
