from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.store.store import Store


@pytest.fixture
def microsalt_fastq_handler(
    base_store: Store, real_housekeeper_api: HousekeeperAPI
) -> MicrosaltFastqHandler:
    return MicrosaltFastqHandler(
        status_db=base_store, housekeeper_api=real_housekeeper_api, root_dir=Path("/dev/null")
    )
