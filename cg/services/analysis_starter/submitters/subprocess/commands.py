from cg.constants import Workflow

WORKFLOW_LAUNCH_COMMAND_MAP: dict[Workflow, str] = {
    Workflow.MICROSALT: "{conda_binary} run --name {environment} "
    "{binary} analyse {config_file} --input {fastq_directory}",
    Workflow.BALSAMIC: "{conda_binary} run {binary} run --account {account} --mail-user {mail_user} "
    "--qos {qos} --sample-config {sample_config} --cluster-config {cluster_config} --run-analysis "
    "--benchmark",
}

WORKFLOW_VERSION_COMMAND_MAP: dict[Workflow, str] = {
    Workflow.MICROSALT: "{conda_binary} run {binary} --version"
}
