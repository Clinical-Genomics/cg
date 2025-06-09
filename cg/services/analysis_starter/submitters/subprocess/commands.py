from cg.constants import Workflow

WORKFLOW_LAUNCH_COMMAND_MAP: dict[Workflow, str] = {
    Workflow.MICROSALT: "{conda_binary} run --name {environment} "
    "{binary} analyse {config_file} --input {fastq_directory}"
}

WORKFLOW_VERSION_COMMAND_MAP: dict[Workflow, str] = {
    Workflow.MICROSALT: "{conda_binary} run {binary} --version"
}
