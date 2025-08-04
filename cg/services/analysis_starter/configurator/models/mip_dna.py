from pydantic import Field

from cg.constants.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MIPDNACaseConfig(CaseConfig):
    bwa_mem: int | None = None
    bwa_mem2: int | None = None
    email: str
    slurm_qos: str
    start_after_recipe: str | None = Field(default=None, alias="start_after")
    start_with_recipe: str | None = Field(default=None, alias="start_with")
    workflow: Workflow = Workflow.MIP_DNA
