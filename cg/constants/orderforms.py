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
    MICROBIAL_FASTQ: str = "microbial_sequencing"
    PACBIO_LONG_READ: str = "pacbio_revio_sequencing"
    TAXPROFILER: str = "1508"

    @staticmethod
    def get_current_orderform_version(order_form: str) -> str:
        """Returns the current version of the given order form."""
        current_order_form_versions = {
            Orderform.MIP_DNA: "32",
            Orderform.RML: "19",
            Orderform.MICROSALT: "11",
            Orderform.SARS_COV_2: "9",
            Orderform.MICROBIAL_FASTQ: "1",
            Orderform.PACBIO_LONG_READ: "1",
        }
        return current_order_form_versions[order_form]


REGION_CODES: dict[str, str] = {
    "Stockholm": "01",
    "Uppsala": "03",
    "Sörmland": "04",
    "Östergötland": "05",
    "Jönköpings län": "06",
    "Kronoberg": "07",
    "Kalmar län": "08",
    "Gotland": "09",
    "Blekinge": "10",
    "Skåne": "12",
    "Halland": "13",
    "Västra Götalandsregionen": "14",
    "Värmland": "17",
    "Örebro län": "18",
    "Västmanland": "19",
    "Dalarna": "20",
    "Gävleborg": "21",
    "Västernorrland": "22",
    "Jämtland Härjedalen": "23",
    "Västerbotten": "24",
    "Norrbotten": "25",
}

ORIGINAL_LAB_ADDRESSES: dict[str, str] = {
    "Unilabs Stockholm": "171 54 Solna",
    "Synlab Medilab": "183 53 Täby",
    "A05 Diagnostics": "171 65 Solna",
    "Karolinska University Hospital Solna": "171 76 Stockholm",
    "Karolinska University Hospital Huddinge": "141 86 Stockholm",
    "LaboratorieMedicinskt Centrum Gotland": "621 84 Visby",
    "Unilabs Eskilstuna Laboratorium": "631 88 Eskilstuna",
    "Norrland University Hospital": "901 85 Umeå",
}
