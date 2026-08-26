from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.priority import SlurmQos
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.sbatch_commands import (
    ERROR_RSYNC_FUNCTION,
    RSYNC_CONTENTS_COMMAND,
)
from cg.services.events import event_publisher
from cg.store.models import Sample

EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT = "external_sample.transfer_completed"


def transfer_sample(cg_config: CGConfig, sample: Sample):
    slurm_api = SlurmAPI()
    customer_internal_id: str = sample.customer.internal_id
    sample_name: str = sample.name
    sbatch_path = Path(cg_config.data_delivery.base_path, f"{customer_internal_id}_{sample_name}")
    destination_path = Path(cg_config.external.hasta % customer_internal_id, sample_name)
    data = {
        "cg.sample_internal_id": sample.internal_id,
        "transfer_completed_at": "$(date +%Y-%m-%dT%H:%M:%S)",
        "cluster_location": destination_path.as_posix(),
    }

    command: str = _get_rsync_command(
        cg_config, customer_internal_id, sample_name, destination_path, data
    )

    sbatch_parameters = Sbatch(
        job_name=f"{customer_internal_id}_{sample_name}_rsync_external_data",
        account=cg_config.data_delivery.account,
        number_tasks=1,
        memory=1,
        log_dir=sbatch_path.as_posix(),
        email=cg_config.data_delivery.mail_user,
        hours=24,
        commands=command,
        error=ERROR_RSYNC_FUNCTION,
        quality_of_service=SlurmQos.NORMAL,
    )
    sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters)
    slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)


def _get_rsync_command(cg_config, customer_internal_id, sample_name, destination_path, data) -> str:
    command: str = (
        RSYNC_CONTENTS_COMMAND.format(
            source_path=Path(cg_config.external.caesar % customer_internal_id, sample_name),
            destination_path=destination_path,
        )
        + "\n"
        + event_publisher.publish_command(
            nats_config=cg_config.nats,
            subject=f"{cg_config.nats.stream}.{EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT}",
            data=data,
        )
    )
    return command
