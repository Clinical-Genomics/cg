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

    # WHEN generating the rsync command
    res = rsync_api.generate_rsync_command(ticket_id=123456, base_path="/home/proj/stage/customers")

    # THEN assert that the returned command is correct
    assert (
        res
        == "rsync -rvL --progress /home/proj/stage/customers/cust000/inbox/123456/ caesar.scilifelab.se:/home/cust000/inbox/123456/"
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

    # WHEN generating the rsync command
    res = rsync_api.generate_covid_rsync_command(ticket_id=123456)

    # THEN assert that the returned command is correct
    assert (
        res
        == "rsync -rvL --progress /home/proj/production/mutant/cases/yellowhog/results/sars-cov-2_123456_results_*.csv caesar.scilifelab.se:/home/cust000/inbox/wwLab_automatisk_hamtning/"
    )
