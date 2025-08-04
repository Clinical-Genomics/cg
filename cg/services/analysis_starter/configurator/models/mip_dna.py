from cg.constants.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MIPDNACaseConfig(CaseConfig):
    binary: str
    conda_binary: str
    config_file: str
    environment: str
    fastq_directory: str
    workflow: Workflow = Workflow.MIP_DNA
