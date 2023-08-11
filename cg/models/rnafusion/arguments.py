from pathlib import Path
from typing import Optional, Union

from pydantic.v1 import BaseModel

from cg.models.workflow.nf_analysis import PipelineParameters


class CommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: Optional[Union[str, Path]]
    resume: Optional[bool]
    profile: Optional[str]
    stub: Optional[bool]
    config: Optional[Union[str, Path]]
    name: Optional[str]
    revision: Optional[str]
    wait: Optional[str]
    id: Optional[str]
    with_tower: Optional[bool]
    use_nextflow: Optional[bool]
    compute_env: Optional[str]
    work_dir: Optional[Union[str, Path]]
    params_file: Optional[Union[str, Path]]


class RnafusionParameters(PipelineParameters):
    """Rnafusion parameters."""

    genomes_base: Path
    input: Path
    outdir: Path
    all: bool = False
    arriba: bool = True
    cram: str = "arriba,starfusion"
    fastp_trim: bool = True
    fusioncatcher: bool = True
    fusioninspector_filter: bool = False
    fusionreport_filter: bool = False
    pizzly: bool = False
    squid: bool = False
    starfusion: bool = True
    trim: bool = False
    trim_tail: int = 50
