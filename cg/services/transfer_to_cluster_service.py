import logging
from datetime import datetime
from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.priority import SlurmQos
from cg.models.cg_config import CGConfig, DataDeliveryConfig
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.sbatch_commands import (
    ERROR_RSYNC_FUNCTION,
    RSYNC_CONTENTS_COMMAND,
)
from cg.services.events import event_publisher
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT = "external_sample.transfer_completed"
RSYNC_SBATCH_SCRIPT: str = "transfer_sample.sh"


def transfer_sample(cg_config: CGConfig, sample: Sample):
    """Submit an sbatch job that rsyncs one external sample to the destination cluster."""
    LOG.info(
        f"Preparing to transfer sample {sample.name} for customer {sample.customer.internal_id}"
    )
    slurm_api = SlurmAPI()
    sbatch_script: Path = _get_sbatch_script(
        sample=sample, rsync_path=cg_config.data_delivery.base_path
    )
    sbatch_command: str = _get_sbatch_command(cg_config=cg_config, sample=sample)
    sbatch_parameters: Sbatch = _get_sbatch_parameters(
        command=sbatch_command,
        data_delivery_config=cg_config.data_delivery,
        sample=sample,
        sbatch_path=sbatch_script,
    )
    sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters)
    slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_script)


def _get_sbatch_script(sample: Sample, rsync_path: str) -> Path:
    timestamp: str = datetime.now().strftime("%y%m%d_%H_%M_%S_%f")
    log_dir = Path(rsync_path, f"{sample.customer.internal_id}_{sample.name}_{timestamp}")
    log_dir.mkdir(parents=True, exist_ok=False)
    LOG.debug(f"Ensured existence of log directory for sample transfer: {log_dir}")
    sbatch_script = Path(log_dir, RSYNC_SBATCH_SCRIPT)
    return sbatch_script


def _get_sbatch_command(cg_config: CGConfig, sample: Sample) -> str:
    source_path = Path(cg_config.external.caesar % sample.customer.internal_id, sample.name)
    LOG.debug(f"Source directory: {source_path}")
    destination_path = Path(cg_config.external.hasta % sample.customer.internal_id, sample.name)
    destination_path.mkdir(parents=True, exist_ok=True)
    LOG.debug(f"Destination directory: {destination_path}")
    event_payload = {
        "cg.sample_internal_id": sample.internal_id,
        "transfer_completed_at": "$(date +%Y-%m-%dT%H:%M:%S)",
        "cluster_location": destination_path.as_posix(),
    }
    command: str = (
        RSYNC_CONTENTS_COMMAND.format(
            source_path=source_path,
            destination_path=destination_path,
        )
        + "\n"
        + event_publisher.publish_command(
            nats_config=cg_config.nats,
            subject=f"{cg_config.nats.stream}.{EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT}",
            data=event_payload,
        )
    )
    return command


def _get_sbatch_parameters(
    command: str, data_delivery_config: DataDeliveryConfig, sample: Sample, sbatch_path: Path
) -> Sbatch:
    sbatch_parameters = Sbatch(
        job_name=f"{sample.customer.internal_id}_{sample.name}_rsync_external_data",
        account=data_delivery_config.account,
        number_tasks=1,
        memory=1,
        log_dir=sbatch_path.parent.as_posix(),
        email=data_delivery_config.mail_user,
        hours=24,
        commands=command,
        error=ERROR_RSYNC_FUNCTION,
        quality_of_service=SlurmQos.NORMAL,
    )
    return sbatch_parameters
