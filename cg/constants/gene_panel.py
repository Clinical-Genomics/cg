"""Gene panel specific constants"""
from cgmodels.cg.constants import StrEnum

GENOME_BUILD_37 = "37"
GENOME_BUILD_38 = "GRCh38"


class MasterList(StrEnum):
    BRAIN: str = "BRAIN"
    CARDIOLOGY: str = "Cardiology"
    CH: str = "CH"
    CTD: str = "CTD"
    DIAB: str = "DIAB"
    ENDO: str = "ENDO"
    EP: str = "EP"
    IBMFS: str = "IBMFS"
    IEM: str = "IEM"
    IF: str = "IF"
    MCARTA: str = "mcarta"
    MHT: str = "MHT"
    MIT: str = "MIT"
    MOVE: str = "MOVE"
    MTDNA: str = "mtDNA"
    NBS_M: str = "NBS-M"
    NEURODEG: str = "NEURODEG"
    NMD: str = "NMD"
    PEDHEP: str = "PEDHEP"
    PID: str = "PID"
    PIDCAD: str = "PIDCAD"
    OMIM_AUTO: str = "OMIM-AUTO"
    SKD: str = "SKD"
    