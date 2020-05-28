"""Fixtures for crunchy api"""

import shutil
import pytest
from pathlib import Path


@pytest.fixture(scope="function")
def crunchy_test_dir(tmpdir_factory):
    """Path to a temporary directory"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="function")
def bam_path(crunchy_test_dir):
    """Creates a BAM path"""
    _bam_path = crunchy_test_dir / "file.bam"
    return _bam_path


@pytest.fixture(scope="function")
def existing_bam_path(bam_path):
    """Creates an existing BAM path"""
    bam_path.touch()
    return bam_path


@pytest.fixture(scope="function")
def compressed_bam(existing_bam_path):
    """Creates BAM with corresponding CRAM, CRAI and FLAG"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    crai_path = bam_path.with_suffix(".cram.crai")
    flag_path = bam_path.with_suffix(".crunchy.txt")
    cram_path.touch()
    crai_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    assert flag_path.exists()
    return bam_path


@pytest.fixture(scope="function")
def compressed_bam_without_crai(existing_bam_path):
    """Creates BAM with corresponding CRAM and FLAG, but no CRAI"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    flag_path = bam_path.with_suffix(".crunchy.txt")
    cram_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert flag_path.exists()
    return bam_path


@pytest.fixture(scope="function")
def compressed_bam_without_flag(existing_bam_path):
    """Creates BAM with corresponding CRAM and FLAG, but no CRAI"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    crai_path = bam_path.with_suffix(".cram.crai")
    cram_path.touch()
    crai_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    return bam_path


@pytest.fixture(scope="function")
def mock_bam_to_cram():
    """ This fixture returns a mocked bam_to_cram method. this mock_method
        Will create files with suffixes .cram and .crai for a given BAM path"""

    def _mock_bam_to_cram_func(bam_path: Path, ntasks: int, mem: int, dry_run: bool = False):

        _ = dry_run
        _ = ntasks
        _ = mem

        cram_path = bam_path.with_suffix(".cram")
        crai_path = bam_path.with_suffix(".cram.crai")
        flag_path = bam_path.with_suffix(".crunchy.txt")

        cram_path.touch()
        crai_path.touch()
        flag_path.touch()

    return _mock_bam_to_cram_func


@pytest.fixture(scope="function")
def sbatch_content(bam_path, crunchy_config_dict):
    """Return expected sbatch content"""
    job_name = bam_path.name + "_bam_to_cram"
    account = crunchy_config_dict["crunchy"]["slurm"]["account"]
    ntasks = 1
    mem = 2
    mail_user = crunchy_config_dict["crunchy"]["slurm"]["mail_user"]
    conda_env = crunchy_config_dict["crunchy"]["slurm"]["conda_env"]
    reference_path = crunchy_config_dict["crunchy"]["cram_reference"]
    cram_path = bam_path.with_suffix(".cram")
    pending_path = bam_path.with_suffix(".crunchy.pending.txt")
    flag_path = bam_path.with_suffix(".crunchy.txt")
    log_dir = bam_path.parent

    _content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={ntasks}
#SBATCH --mem={mem}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={mail_user}
#SBATCH --time=4:00:00
#SBATCH --qos=low

set -e

echo "Running on: $(hostname)"

source activate {conda_env}


error() {{
    if [[ -e {cram_path} ]]
    then
        rm {cram_path}
    fi

    if [[ -e {cram_path}.crai ]]
    then
        rm {cram_path}.crai
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -r {reference_path} -t 12 compress bam -b {bam_path} -c {cram_path}
samtools quickcheck {cram_path}
touch {flag_path}
rm {pending_path}"""

    return _content
