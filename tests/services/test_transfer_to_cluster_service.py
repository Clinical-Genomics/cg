from pathlib import Path
from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.cg_config import CGConfig, DataDeliveryConfig
from cg.services import transfer_to_cluster_service


def test_transfer_sample(mocker: MockerFixture):
    # GIVEN a customer internal id and a sample name
    customer_internal_id = "cust000"
    sample_name = "sample-name"

    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
        data_delivery=DataDeliveryConfig(
            account="account",
            base_path="/base/path",
            covid_destination_path="/covid",
            covid_report_path="/covid/report",
            destination_path="/unknown",
            mail_user="mail@scilifelab.se",
        ),
    )

    submit_sbatch_mock = mocker.patch.object(SlurmAPI, "submit_sbatch")

    # WHEN transfer_sample is called
    transfer_to_cluster_service.transfer_sample(
        cg_config=cg_config, customer_internal_id=customer_internal_id, sample_name=sample_name
    )

    # THEN the Slurm API should have been called with an SBATCH with the correct content
    submit_sbatch_mock.assert_called_once_with(
        sbatch_path=Path("/base", "path", "cust000_sample-name")
    )
