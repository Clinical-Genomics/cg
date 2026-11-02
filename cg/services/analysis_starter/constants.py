from cg.constants import Workflow

IMPLEMENTED_WORKFLOWS_WITH_COMPRESSION = [
    Workflow.BALSAMIC,
    Workflow.BALSAMIC_UMI,
    Workflow.MICROSALT,
    Workflow.MIP_DNA,
    Workflow.RAREDISEASE,
    Workflow.RNAFUSION,
    Workflow.TAXPROFILER,
    Workflow.TOMTE,
]

WORKFLOWS_WITHOUT_COMPRESSION = [Workflow.NALLO, Workflow.TRANA_16S, Workflow.TRANA_ITS]
