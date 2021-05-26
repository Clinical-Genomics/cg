import logging
from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.slurm.sbatch import Sbatch


def test_instantiate_slurm_api():
    # GIVEN nothing

    # WHEN instantiating the slurm api
    api = SlurmAPI()

    # THEN assert dry_run is set to False
    assert api.dry_run is False

    # THEN assert that the process is sbatch
    assert api.process.binary == "sbatch"


def test_generate_sbatch_header(sbatch_parameters: Sbatch):
    # GIVEN a Sbatch object with some parameters

    # WHEN building a sbatch header
    sbatch_header: str = SlurmAPI.generate_sbatch_header(sbatch_parameters)

    # THEN assert that the email adress was added
    assert f"#SBATCH --mail-user={sbatch_parameters.email}" in sbatch_header


def test_generate_sbatch_body_no_error_function(sbatch_parameters: Sbatch):
    # GIVEN a Sbatch object with some parameters

    # WHEN building a sbatch header
    sbatch_body: str = SlurmAPI.generate_sbatch_body(commands=sbatch_parameters.commands)

    # THEN assert that the email adress was added
    assert "log 'Something went wrong, aborting'" in sbatch_body


def test_generate_sbatch_script(sbatch_parameters: Sbatch):
    # GIVEN a SlurmAPI
    api = SlurmAPI()
    # GIVEN a Sbatch object with some parameters

    # WHEN creating a sbatch script
    sbatch_content: str = api.generate_sbatch_content(sbatch_parameters=sbatch_parameters)

    # THEN assert that the command is in the body
    assert sbatch_parameters.commands in sbatch_content


def test_submit_sbatch_script_dry_run(sbatch_content: str):
    # GIVEN a sbatch file
    # GIVEN a slurm api in dry run
    api = SlurmAPI()
    api.set_dry_run(dry_run=True)
    # GIVEN the path to a file
    outfile = Path("hello")

    # WHEN submitting the sbatch job
    job_number: int = api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=outfile)

    # THEN assert that a job number is returned
    assert isinstance(job_number, int)


def test_submit_sbatch_script(sbatch_content: str, slurm_api: SlurmAPI, sbatch_path: Path):
    # GIVEN a slurm api
    # GIVEN some sbatch content
    # GIVEN the path to a sbatch file

    # WHEN submitting the job
    job_number: int = slurm_api.submit_sbatch(
        sbatch_content=sbatch_content, sbatch_path=sbatch_path
    )

    # THEN assert that a job number is returned
    assert isinstance(job_number, int)


def test_submit_sbatch_script_std_error_output(
    sbatch_content: str, slurm_api: SlurmAPI, sbatch_path: Path, sbatch_job_number: int, caplog
):
    caplog.set_level(logging.INFO)
    # GIVEN a slurm api
    # GIVEN some sbatch content
    # GIVEN the path to a sbatch file
    # GIVEN that the slurm system responds with some standard error information
    message = "Something might be an error"
    slurm_api.process.set_stderr(text=message)

    # WHEN submitting the job
    job_number: int = slurm_api.submit_sbatch(
        sbatch_content=sbatch_content, sbatch_path=sbatch_path
    )

    # THEN assert that the message was logged
    assert message in caplog.text

    # THEN assert that the correct job number is returned regardless of the error
    assert job_number == sbatch_job_number


def test_submit_sbatch_script_alternative_sbatch_response(
    sbatch_content: str, slurm_api: SlurmAPI, sbatch_path: Path, sbatch_job_number: int
):
    # GIVEN a slurm api
    # GIVEN some sbatch content
    # GIVEN the path to a sbatch file
    # GIVEN that the slurm system responds slightly different
    slurm_api.process.set_stdout(text=f"Submitted batch {sbatch_job_number}")

    # WHEN submitting the job
    job_number: int = slurm_api.submit_sbatch(
        sbatch_content=sbatch_content, sbatch_path=sbatch_path
    )

    # THEN assert that a job number is returned
    assert job_number == sbatch_job_number


def test_submit_sbatch_script_invalid_sbatch_response(
    sbatch_content: str, slurm_api: SlurmAPI, sbatch_path: Path
):
    # GIVEN a slurm api
    # GIVEN some sbatch content
    # GIVEN the path to a sbatch file
    # GIVEN that the slurm system responds with something unexpected
    slurm_api.process.set_stdout(text=f"something went wrong")

    # WHEN submitting the job
    job_number: int = slurm_api.submit_sbatch(
        sbatch_content=sbatch_content, sbatch_path=sbatch_path
    )

    # THEN assert that a job number 0 indicating malfunction
    assert job_number == 0
