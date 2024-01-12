from pathlib import Path

import click


def get_config_path(context: click.Context) -> str:
    return Path(context.obj.data_delivery.base_path, "slurm_job_ids.yaml").as_posix()
