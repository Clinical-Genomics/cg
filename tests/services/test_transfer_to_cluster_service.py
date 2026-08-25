from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.cg_config import CGConfig, DataDeliveryConfig, ExternalConfig
from cg.services import transfer_to_cluster_service


@pytest.fixture
def expected_sbatch_content() -> str:
    return """#! /bin/bash \n#SBATCH --job-name=cust000_sample-name_rsync_external_data
#SBATCH --account=account
#SBATCH --ntasks=1
#SBATCH --mem=1G
#SBATCH --error=/base/path/cust000_sample-name/cust000_sample-name_rsync_external_data.stderr
#SBATCH --output=/base/path/cust000_sample-name/cust000_sample-name_rsync_external_data.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=mail@scilifelab.se
#SBATCH --time=24:00:00
#SBATCH --qos=normal


set -eu -o pipefail

log() {
    NOW=$(date +"%Y-%m-%dT%H:%M:%S")
    echo "[${NOW}] $*" 1>&2;
}

log "Running on: $(hostname)"


error() {
    \necho "Rsync failed"

    exit 1
}

trap error ERR


rsync -rvL /path/to/rome/cust000/sample-name/ /path/to/hasta/cust000/sample-name


"""


def test_transfer_sample(mocker: MockerFixture, expected_sbatch_content):
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
        external=ExternalConfig(hasta="/path/to/hasta/%s", caesar="/path/to/rome/%s"),
    )

    submit_sbatch_mock = mocker.patch.object(SlurmAPI, "submit_sbatch")

    # WHEN transfer_sample is called
    transfer_to_cluster_service.transfer_sample(
        cg_config=cg_config, customer_internal_id=customer_internal_id, sample_name=sample_name
    )

    # THEN the Slurm API should have been called with an SBATCH with the correct content
    submit_sbatch_mock.assert_called_once_with(
        sbatch_path=Path("/base", "path", "cust000_sample-name"),
        sbatch_content=expected_sbatch_content,
    )
