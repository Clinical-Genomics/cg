from cg.constants import Workflow
from cg.models.orders.constants import OrderType

ORDER_TYPE_WORKFLOW_MAP: dict[OrderType, Workflow] = {
    OrderType.BALSAMIC: Workflow.BALSAMIC,
    OrderType.BALSAMIC_UMI: Workflow.BALSAMIC_UMI,
    OrderType.FASTQ: Workflow.RAW_DATA,
    OrderType.FLUFFY: Workflow.FLUFFY,
    OrderType.METAGENOME: Workflow.RAW_DATA,
    OrderType.MICROBIAL_FASTQ: Workflow.RAW_DATA,
    OrderType.MICROSALT: Workflow.MICROSALT,
    OrderType.MIP_DNA: Workflow.MIP_DNA,
    OrderType.MIP_RNA: Workflow.MIP_RNA,
    OrderType.NALLO: Workflow.NALLO,
    OrderType.PACBIO_LONG_READ: Workflow.RAW_DATA,
    OrderType.RAREDISEASE: Workflow.RAREDISEASE,
    OrderType.RML: Workflow.RAW_DATA,
    OrderType.RNAFUSION: Workflow.RNAFUSION,
    OrderType.SARS_COV_2: Workflow.MUTANT,
    OrderType.TAXPROFILER: Workflow.TAXPROFILER,
    OrderType.TOMTE: Workflow.TOMTE,
}
