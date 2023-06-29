"""Gene panel specific constants."""
from typing import List

from cg.utils.enums import StrEnum

GENOME_BUILD_37 = "37"
GENOME_BUILD_38 = "GRCh38"


class GenePanelMasterList(StrEnum):
    BRAIN: str = "BRAIN"
    CARDIOLOGY: str = "Cardiology"
    CILM: str = "CILM"
    CH: str = "CH"
    CTD: str = "CTD"
    DIAB: str = "DIAB"
    ENDO: str = "ENDO"
    EP: str = "EP"
    HEARING: str = "HEARING"
    HYDRO: str = "HYDRO"
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
    OMIM_AUTO: str = "OMIM-AUTO"
    PANELAPP_GREEN: str = "PANELAPP-GREEN"
    PEDHEP: str = "PEDHEP"
    PID: str = "PID"
    PIDCAD: str = "PIDCAD"
    RETINA: str = "RETINA"
    SKD: str = "SKD"
    SOVM: str = "SOVM"
    STROKE: str = "STROKE"

    @classmethod
    def get_panel_names(cls, panels=None) -> List[str]:
        """Return requested panel names from Master list, or all panels if none are specified."""
        return (
            [panel_name.value for panel_name in panels]
            if panels
            else list(map(lambda panel: panel.value, cls))
        )
