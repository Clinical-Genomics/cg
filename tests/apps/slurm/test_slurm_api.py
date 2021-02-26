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


def tes_generate_sbatch_header(sbatch_parameters: Sbatch):
    # GIVEN a Sbatch object with some parameters

    # WHEN building a sbatch header
    sbatch_header: str = SlurmAPI.generate_sbatch_header(sbatch_parameters)

    # THEN assert that the email adress was added
    assert f"#SBATCH --mail-user={sbatch_parameters.email}" in sbatch_header
