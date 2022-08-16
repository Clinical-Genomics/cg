from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.models.orders.order import OrderType
from cg.utils.enums import StrEnum

SEX_MAP = {"male": "M", "female": "F", "unknown": "unknown"}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
CONTAINER_TYPES = ["Tube", "96 well plate"]
SOURCE_TYPES = set().union(METAGENOME_SOURCES, ANALYSIS_SOURCES)

CASE_PROJECT_TYPES = [
    str(OrderType.MIP_DNA),
    str(OrderType.BALSAMIC),
    str(OrderType.MIP_RNA),
]


class Orderform(StrEnum):
    BALSAMIC: str = "1508"
    BALSAMIC_QC: str = "1508"
    BALSAMIC_UMI: str = "1508"
    FASTQ: str = "1508"
    FLUFFY: str = "1604"
    METAGENOME: str = "1605"
    MICROSALT: str = "1603"
    MIP_DNA: str = "1508"
    MIP_RNA: str = "1508"
    RML: str = "1604"
    SARS_COV_2: str = "2184"


ORDERFORM_VERSIONS = {
    Orderform.MIP_DNA: "27",
    Orderform.RML: "15",
    Orderform.METAGENOME: "10",
    Orderform.MICROSALT: "11",
    Orderform.SARS_COV_2: "7",
}
