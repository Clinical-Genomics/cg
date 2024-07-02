"""Gene panel specific constants."""

from enum import StrEnum

from cg.constants.constants import CustomerId

GENOME_BUILD_37: str = "37"
GENOME_BUILD_38: str = "GRCh38"


class GenePanelGenomeBuild(StrEnum):
    hg19: str = GENOME_BUILD_37
    hg38: str = GENOME_BUILD_38


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

    @staticmethod
    def is_customer_collaborator_and_panels_in_gene_panels_master_list(
        customer_id: str, gene_panels: set[str]
    ) -> bool:
        return customer_id in GenePanelMasterList.collaborators() and gene_panels.issubset(
            GenePanelMasterList.get_panel_names()
        )

    @staticmethod
    def get_non_specific_gene_panels() -> set[str]:
        return {GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN}


class GenePanelCombo:
    COMBO_1: dict[str, set[str]] = {
        "DSD": {"DSD", "DSD-S", "HYP", "POI"},
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
