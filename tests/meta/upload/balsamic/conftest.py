from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from tests.cli.workflow.balsamic.conftest import *


@pytest.fixture(scope="function", name="balsamic_upload_api")
def fixture_balsamic_upload_api(balsamic_context: CGConfig) -> BalsamicUploadAPI:
    yield BalsamicUploadAPI(balsamic_context.status_db)