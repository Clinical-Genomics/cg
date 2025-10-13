from enum import StrEnum

from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES

SEX_MAP = {"male": "M", "female": "F", "unknown": "unknown"}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
SOURCE_TYPES = set().union(METAGENOME_SOURCES, ANALYSIS_SOURCES)


class Orderform(StrEnum):
    BALSAMIC = "1508"
    BALSAMIC_UMI = "1508"
    FASTQ = "1508"
    METAGENOME = "1508"
    FLUFFY = "1604"
    MICROSALT = "1603"
    MIP_DNA = "1508"
    MIP_RNA = "1508"
    NALLO = "long_read_nallo_analysis"
    RAREDISEASE = "1508"
    RNAFUSION = "1508"
    RML = "1604"
    SARS_COV_2 = "2184"
    MICROBIAL_FASTQ = "microbial_sequencing"
    PACBIO_LONG_READ = "pacbio_revio_sequencing"
    TAXPROFILER = "1508"
    TOMTE = "1508"

    @staticmethod
    def get_current_orderform_version(order_form: str) -> str:
        """Returns the current version of the given order form."""
        current_order_form_versions = {
            Orderform.MIP_DNA: "35",
            Orderform.RML: "20",
            Orderform.MICROSALT: "12",
            Orderform.NALLO: "1",
            Orderform.SARS_COV_2: "10",
            Orderform.MICROBIAL_FASTQ: "3",
            Orderform.PACBIO_LONG_READ: "2",
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
    "Länssjukhuset Sundsvall": "856 43 Sundsvall",
}
