"""Gene panel specific constants."""

from enum import StrEnum

from cg.constants.constants import CustomerId

GENOME_BUILD_37: str = "37"
GENOME_BUILD_38: str = "GRCh38"


class GenePanelGenomeBuild(StrEnum):
    hg19 = GENOME_BUILD_37
    hg38 = GENOME_BUILD_38


class GenePanelMasterList(StrEnum):
    BRAIN = "BRAIN"
    CARDIOLOGY = "Cardiology"
    CILM = "CILM"
    CH = "CH"
    CHILDHYPOTONIA = "CHILDHYPOTONIA"
    CTD = "CTD"
    DIAB = "DIAB"
    ENDO = "ENDO"
    EP = "EP"
    HEARING = "HEARING"
    HYDRO = "HYDRO"
    IBMFS = "IBMFS"
    IEM = "IEM"
    IF = "IF"
    MCARTA = "mcarta"
    MHT = "MHT"
    MIT = "MIT"
    MOVE = "MOVE"
    MTDNA = "mtDNA"
    NBS_M = "NBS-M"
    NEURODEG = "NEURODEG"
    NMD = "NMD"
    OMIM_AUTO = "OMIM-AUTO"
    OPTIC = "OPTIC"
    PANELAPP_GREEN = "PANELAPP-GREEN"
    PEDHEP = "PEDHEP"
    PID = "PID"
    PIDCAD = "PIDCAD"
    RETINA = "RETINA"
    SKD = "SKD"
    SOVM = "SOVM"
    STROKE = "STROKE"
    AID = "AID"
    INHERITED_CANCER = "Inherited cancer"
    VEO_IBD = "VEO-IBD"
    KIDNEY = "Kidney"
    CAKUT = "CAKUT"
    NCRNA = "ncRNA"

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
