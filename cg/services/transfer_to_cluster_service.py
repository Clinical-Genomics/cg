from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI


def transfer_sample(customer_internal_id: str, sample_name: str):
    # TODO submit a slurm job that calls rsync to transfer sample data from customer inbox to hasta
    slurm_api = SlurmAPI()
    sbatch_path = Path("?")
    sbatch_content = ""
    slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
    # TODO publish an event when successful
    pass
