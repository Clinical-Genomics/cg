"""Gene panel specific constants."""

from enum import StrEnum

from cg.constants.constants import CustomerId

GENOME_BUILD_37: str = "37"
GENOME_BUILD_38: str = "GRCh38"


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
    OPTIC: str = "OPTIC"
    PANELAPP_GREEN: str = "PANELAPP-GREEN"
    PEDHEP: str = "PEDHEP"
    PID: str = "PID"
    PIDCAD: str = "PIDCAD"
    RETINA: str = "RETINA"
    SKD: str = "SKD"
    SOVM: str = "SOVM"
    STROKE: str = "STROKE"
    AID: str = "AID"
    INHERITED_CANCER: str = "Inherited cancer"

    @classmethod
    def get_panel_names(cls, panels=None) -> list[str]:
        """Return requested panel names from the Master list, or all panels if none are specified."""
        return list(panels) if panels else list(map(lambda panel: panel.value, cls))

    @staticmethod
    def collaborators() -> set[str]:
        """Return collaborators of the Master list."""
        return {
            CustomerId.CG_INTERNAL_CUSTOMER,
            CustomerId.CUST002,
            CustomerId.CUST003,
            CustomerId.CUST004,
            CustomerId.CUST042,
        }


class GenePanelCombo:
    COMBO_1: dict[str, set[str]] = {
        "DSD": {"DSD", "DSD-S", "HYP", "SEXDIF", "SEXDET"},
        "CM": {"CNM", "CM"},
        "Horsel": {"Horsel", "141217", "141201"},
        "OPHTHALMO": {
            "OPHTHALMO",
            "ANTE-ED",
            "CATARACT",
            "CORNEA",
            "GLAUCOMA",
            "RETINA",
            "SED",
            "ALBINISM",
        },
    }
