from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.priority import SlurmQos
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.sbatch_commands import (
    ERROR_RSYNC_FUNCTION,
    RSYNC_CONTENTS_COMMAND,
)
from cg.services.events.event_publisher import publish_command
from cg.store.models import Sample


def transfer_sample(cg_config: CGConfig, sample: Sample):
    # TODO submit a slurm job that calls rsync to transfer sample data from customer inbox to hasta
    slurm_api = SlurmAPI()
    customer_internal_id: str = sample.customer.internal_id
    sample_name: str = sample.name
    sbatch_path = Path(cg_config.data_delivery.base_path, f"{customer_internal_id}_{sample_name}")
    command: str = RSYNC_CONTENTS_COMMAND.format(
        source_path=Path(cg_config.external.caesar % customer_internal_id, sample_name),
        destination_path=Path(cg_config.external.hasta % customer_internal_id, sample_name),
    )

    data = {
        "cg.analysis_id": analysis_id,
        "uploaded_at": "$(date +%Y-%m-%dT%H:%M:%SZ)",
    }
    command += "\n" + publish_command(
        nats_config=cg_config.nats,
        subject=f"{cg_config.nats.stream}.{ANALYSIS_UPLOADED_SUBJECT}",
        data=data,
    )

    # TODO add a publisher to the slurm job
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
    # TODO publish an event when successful
    pass
