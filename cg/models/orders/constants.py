from cgmodels.cg.constants import Pipeline, StrEnum


class OrderType(StrEnum):
    BALSAMIC: str = str(Pipeline.BALSAMIC)
    BALSAMIC_QC: str = str(Pipeline.BALSAMIC_QC)
    BALSAMIC_UMI: str = str(Pipeline.BALSAMIC_UMI)
    FASTQ: str = str(Pipeline.FASTQ)
    FLUFFY: str = str(Pipeline.FLUFFY)
    METAGENOME: str = "metagenome"
    MICROSALT: str = str(Pipeline.MICROSALT)
    MIP_DNA: str = str(Pipeline.MIP_DNA)
    MIP_RNA: str = str(Pipeline.MIP_RNA)
    RML: str = "rml"
    RNAFUSION: str = str(Pipeline.RNAFUSION)
    SARS_COV_2: str = str(Pipeline.SARS_COV_2)
