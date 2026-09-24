from cg.constants import Workflow

WORKFLOW_VERSION_COMMAND_MAP: dict[Workflow, str] = {
    Workflow.MICROSALT: "{conda_binary} run {binary} --config {pipeline_config_path} --version"
}
