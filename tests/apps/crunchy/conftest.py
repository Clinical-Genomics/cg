"""Fixtures for crunchy api"""
import copy
import logging
from pathlib import Path
from typing import List

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX

LOG = logging.getLogger(__name__)


class MockProcess:
    """Mock a process"""

    def __init__(self, process_name: str):
        """Inititalise mock"""
        self.stderr = ""
        self.stdout = ""
        self.base_call = [process_name]
        self.process_name = process_name

    def run_command(self, parameters: List):
        """Mock the run process method"""
        command = copy.deepcopy(self.base_call)
        if parameters:
            command.extend(parameters)

        LOG.info("Running command %s", " ".join(command))


@pytest.fixture(scope="function", name="sbatch_process")
def fixture_sbatch_process():
    """Return a mocked process object"""
    return MockProcess("sbatch")


@pytest.fixture(scope="function", name="bam_path")
def fixture_bam_path(project_dir):
    """Creates a BAM path"""
    _bam_path = project_dir / "file.bam"
    return _bam_path


@pytest.fixture(scope="function", name="existing_bam_path")
def fixture_existing_bam_path(bam_path):
    """Creates an existing BAM path"""
    bam_path.touch()
    return bam_path


@pytest.fixture(scope="function", name="compressed_bam")
def fixture_compressed_bam(existing_bam_path):
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


@pytest.fixture(scope="function", name="compressed_bam_without_crai")
def fixture_compressed_bam_without_crai(existing_bam_path):
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


@pytest.fixture(scope="function", name="compressed_bam_without_flag")
def fixture_compressed_bam_without_flag(existing_bam_path):
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


@pytest.fixture(scope="function", name="fastq_paths")
def fixture_fastq_paths(project_dir):
    """Creates fastq paths"""
    _fastq_first_path = project_dir / ("file" + FASTQ_FIRST_READ_SUFFIX)
    _fastq_second_path = project_dir / ("file" + FASTQ_SECOND_READ_SUFFIX)
    return {
        "fastq_first_path": _fastq_first_path,
        "fastq_second_path": _fastq_second_path,
    }


@pytest.fixture(scope="function", name="existing_fastq_paths")
def fixture_existing_fastq_paths(fastq_paths):
    """Creates existing FASTQ paths"""
    for _, fastq_path in fastq_paths.items():
        fastq_path.touch()
        assert fastq_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs")
def fixture_compressed_fastqs(existing_fastq_paths):
    """Creates fastqs with corresponding SPRING and FLAG"""
    fastq_paths = existing_fastq_paths
    spring_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(FASTQ_FIRST_READ_SUFFIX, ".spring")
    )
    flag_path = spring_path.with_suffix("").with_suffix(".json")

    spring_path.touch()
    flag_path.touch()
    assert spring_path.exists()
    assert flag_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_without_spring")
def fixture_compressed_fastqs_without_spring(existing_fastq_paths):
    """Creates fastqs with corresponding FLAG"""
    fastq_paths = existing_fastq_paths
    flag_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(FASTQ_FIRST_READ_SUFFIX, ".crunchy.txt")
    )
    flag_path.touch()
    assert flag_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_without_flag")
def fixture_compressed_fastqs_without_flag(existing_fastq_paths):
    """Creates fastqs with corresponding SPRING"""
    fastq_paths = existing_fastq_paths
    spring_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(FASTQ_FIRST_READ_SUFFIX, ".spring")
    )
    spring_path.touch()
    assert spring_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_pending")
def fixture_compressed_fastqs_pending(existing_fastq_paths):
    """Creates fastqs with corresponding PENDING"""
    fastq_paths = existing_fastq_paths
    pending_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(
            FASTQ_FIRST_READ_SUFFIX, ".crunchy.pending.txt"
        )
    )
    pending_path.touch()
    assert pending_path.exists()
    return fastq_paths


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


@pytest.fixture(scope="function", name="sbatch_content")
def fixture_sbatch_content(bam_path, crunchy_config_dict):
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


@pytest.fixture(scope="function", name="sbatch_content_spring")
def fixture_sbatch_content_spring(fastq_paths, crunchy_config_dict):
    """Return expected sbatch content for spring job"""
    job_name = str(fastq_paths["fastq_first_path"].name).replace(
        FASTQ_FIRST_READ_SUFFIX, "_fastq_to_spring"
    )
    account = crunchy_config_dict["crunchy"]["slurm"]["account"]
    ntasks = 1
    mem = 2
    mail_user = crunchy_config_dict["crunchy"]["slurm"]["mail_user"]
    conda_env = crunchy_config_dict["crunchy"]["slurm"]["conda_env"]
    fastq_first = fastq_paths["fastq_first_path"]
    fastq_second = fastq_paths["fastq_second_path"]
    spring_path = CrunchyAPI.get_spring_path_from_fastq(fastq_first)
    pending_path = CrunchyAPI.get_pending_path(fastq_first)
    log_dir = fastq_paths["fastq_first_path"].parent

    _content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={ntasks}
#SBATCH --mem={mem}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={mail_user}
#SBATCH --time=24:00:00
#SBATCH --qos=low

set -e

echo "Running on: $(hostname)"

source activate {conda_env}


error() {{
    if [[ -e {spring_path} ]]
    then
        rm {spring_path}
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -t 12 compress fastq -f {fastq_first} -s {fastq_second} -o {spring_path} --check-integrity --metadata-file
rm {pending_path}"""

    return _content
