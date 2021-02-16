from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.meta.orders import OrderType

SEX_MAP = {"male": "M", "female": "F", "unknown": "unknown"}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
CONTAINER_TYPES = ["Tube", "96 well plate"]
SOURCE_TYPES = set().union(METAGENOME_SOURCES, ANALYSIS_SOURCES)

CASE_PROJECT_TYPES = [
    str(OrderType.MIP_DNA),
    str(OrderType.EXTERNAL),
    str(OrderType.BALSAMIC),
    str(OrderType.MIP_RNA),
]
