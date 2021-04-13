"""Tests for rsync API"""

from cg.meta.rsync import RsyncAPI
from cg.store import Store


def test_generate_rsync_command(analysis_store_single_case: Store, mocker):
    """Test generating the rsync command"""

    # GIVEN a populated rsync api
    rsync_api = RsyncAPI(store=analysis_store_single_case)

    # GIVEN the customer id is cust000
    mocker.patch.object(RsyncAPI, "get_customer_id")
    RsyncAPI.get_customer_id.return_value = "cust000"

    # GIVEN source and destination paths for the rsync command
    paths = {
        "base_source_path": "/test/folder",
        "destination_path": "server.name.se:/some/%s/path/%s/",
        "covid_destination_path": "server.name.se:/another/%s/foldername/",
        "covid_source_path": "/folder_structure/%s/yet_another_folder/filename_%s_data_*.csv ",
    }

    # WHEN generating the rsync command
    res = rsync_api.generate_rsync_command(ticket_id=123456, paths=paths)

    # THEN assert that the returned command is correct
    assert (
        res
        == "rsync -rvL /test/folder/cust000/inbox/123456/ server.name.se:/some/cust000/path/123456/"
    )


def test_generate_covid_rsync_command(analysis_store_single_case: Store, mocker):
    """Test generating the rsync command for covid samples"""

    # GIVEN a populated rsync api
    rsync_api = RsyncAPI(store=analysis_store_single_case)

    # GIVEN the case id is yellowhog
    mocker.patch.object(RsyncAPI, "get_case_id")
    RsyncAPI.get_case_id.return_value = "yellowhog"

    # GIVEN the customer id is cust000
    mocker.patch.object(RsyncAPI, "get_customer_id")
    RsyncAPI.get_customer_id.return_value = "cust000"

    # GIVEN source and destination paths for the rsync command
    paths = {
        "base_source_path": "/test/folder",
        "destination_path": "server.name.se:/some/%s/path/%s/",
        "covid_destination_path": "server.name.se:/another/%s/foldername/",
        "covid_source_path": "/folder_structure/%s/yet_another_folder/filename_%s_data_*.csv ",
    }

    # WHEN generating the rsync command
    res = rsync_api.generate_covid_rsync_command(ticket_id=123456, paths=paths)

    # THEN assert that the returned command is correct
    assert (
        res
        == "rsync -rvL /folder_structure/yellowhog/yet_another_folder/filename_123456_data_*.csv server.name.se:/another/cust000/foldername/"
    )
