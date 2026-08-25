from pytest_mock import MockerFixture

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.services import transfer_to_cluster_service


def test_transfer_sample(mocker: MockerFixture):
    # GIVEN a customer internal id and a sample name
    customer_internal_id = "cust000"
    sample_name = "sample-name"

    submit_sbatch_mock = mocker.patch.object(SlurmAPI, "submit_sbatch")

    # WHEN transfer_sample is called
    transfer_to_cluster_service.transfer_sample(customer_internal_id, sample_name)

    # THEN the Slurm API should have been called with an SBATCH with the correct content
    submit_sbatch_mock.assert_called_once_with("?")
