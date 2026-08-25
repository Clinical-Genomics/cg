from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.cg_config import CGConfig


def transfer_sample(cg_config: CGConfig, customer_internal_id: str, sample_name: str):
    # TODO submit a slurm job that calls rsync to transfer sample data from customer inbox to hasta
    slurm_api = SlurmAPI()
    sbatch_path = Path(cg_config.data_delivery.base_path, f"{customer_internal_id}_{sample_name}")
    sbatch_content = ""
    slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
    # TODO publish an event when successful
    pass
