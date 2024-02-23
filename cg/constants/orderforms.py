from enum import StrEnum

from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.models.orders.order import OrderType

SEX_MAP = {"male": "M", "female": "F", "unknown": "unknown"}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
CONTAINER_TYPES = ["Tube", "96 well plate"]
SOURCE_TYPES = set().union(METAGENOME_SOURCES, ANALYSIS_SOURCES)

CASE_PROJECT_TYPES = [
    OrderType.MIP_DNA,
    OrderType.BALSAMIC,
    OrderType.MIP_RNA,
]


class Orderform(StrEnum):
    BALSAMIC: str = "1508"
    BALSAMIC_QC: str = "1508"
    BALSAMIC_UMI: str = "1508"
    FASTQ: str = "1508"
    METAGENOME: str = "1508"
    FLUFFY: str = "1604"
    MICROSALT: str = "1603"
    MIP_DNA: str = "1508"
    MIP_RNA: str = "1508"
    RNAFUSION: str = "1508"
    RML: str = "1604"
    SARS_COV_2: str = "2184"

    @staticmethod
    def get_current_orderform_version(order_form: str) -> str:
        """Returns the current version of the given order form."""
        current_order_form_versions = {
            Orderform.MIP_DNA: "30",
            Orderform.RML: "17",
            Orderform.MICROSALT: "11",
            Orderform.SARS_COV_2: "8",
        }
        return current_order_form_versions[order_form]
