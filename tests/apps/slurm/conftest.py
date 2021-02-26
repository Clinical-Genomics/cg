import pytest
from cg.models.slurm.sbatch import Sbatch


@pytest.fixture(name="sbatch_parmeters")
def fixture_sbatch_parameters(email_adress: str, slurm_account: str) -> Sbatch:
    config = {
        "job_name": "test",
        "account": slurm_account,
        "number_tasks": 3,
        "memory": 10,
        "log_dir": "path/to/dir",
        "email": email_adress,
        "hours": 2,
        "commands": "genmod",
    }
    return Sbatch.parse_obj(config)
