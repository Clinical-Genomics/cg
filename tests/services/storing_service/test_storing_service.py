from unittest.mock import create_autospec

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.storing_service.store_analysis_service import store_analysis_output


def test_store_pipeline_output_success():

    # GIVEN a case id with all mandatory files present
    # GIVEN a case_deliverables file for that given case
    # GIVEN a HousekeeperAPI
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    # WHEN storing the pipeline outputs
    store_analysis_output(
        root_directory=Path("root_directory"), case_id="case_id", housekeeper_api=housekeeper_api
    )
    # THEN the housekeeper bundle for the case should have been created
    pass
