from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig, DataDeliveryConfig, ExternalConfig, NatsConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import Customer, Sample


@pytest.fixture
def expected_sbatch_content() -> str:
    return """#! /bin/bash \n#SBATCH --job-name=cust000_sample-name_rsync_external_data
#SBATCH --account=account
#SBATCH --ntasks=1
#SBATCH --mem=1G
#SBATCH --error=/base/path/cust000_sample-name_080910_10_28_00_000000/cust000_sample-name_rsync_external_data.stderr
#SBATCH --output=/base/path/cust000_sample-name_080910_10_28_00_000000/cust000_sample-name_rsync_external_data.stdout
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

/nats/binary pub --jetstream --server nats://server --tlsca /ca/cert --tlscert /client/cert --tlskey /client/key --token $(cat /token) cg-test.external_sample.transfer_completed "{\\"cg.sample_internal_id\\": \\"ACC1\\", \\"transfer_completed_at\\": \\"$(date +%Y-%m-%dT%H:%M:%S)\\", \\"cluster_location\\": \\"/path/to/hasta/cust000/sample-name\\"}"

"""


@pytest.mark.freeze_time("2008-09-10 10:28:00.00")
def test_transfer_sample(mocker: MockerFixture, expected_sbatch_content):
    # GIVEN a sample and customer
    customer = create_autospec(Customer, internal_id="cust000")
    sample = create_autospec(Sample, internal_id="ACC1", customer=customer)
    sample.name = "sample-name"

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
        nats=NatsConfig(
            nats_binary_path=Path("/nats/binary"),
            server="nats://server",
            stream="cg-test",
            ca_cert_path=Path("/ca/cert"),
            client_cert_path=Path("/client/cert"),
            client_key_path=Path("/client/key"),
            token_path=Path("/token"),
        ),
    )

    # GIVEN that paths are created
    mocker.patch.object(transfer_to_cluster_service.Path, "mkdir")

    # GIVEN a SlurmAPI
    submit_sbatch_mock = mocker.patch.object(transfer_to_cluster_service.SlurmAPI, "submit_sbatch")

    # WHEN transfer_sample is called
    transfer_to_cluster_service.transfer_sample(cg_config=cg_config, sample=sample)

    # THEN the Slurm API should have been called with an SBATCH with the correct content
    submit_sbatch_mock.assert_called_once_with(
        sbatch_path=Path(
            "/base", "path", "cust000_sample-name_080910_10_28_00_000000", "transfer_sample.sh"
        ),
        sbatch_content=expected_sbatch_content,
    )
