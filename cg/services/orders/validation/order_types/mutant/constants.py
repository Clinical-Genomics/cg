from enum import StrEnum

from cg.constants import DataDelivery


class MutantDeliveryType(StrEnum):
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY


class PreProcessingMethod(StrEnum):
    COVID_PRIMER = "Qiagen SARS-CoV-2 Primer Panel"
    COVID_SEQUENCING = "COVIDSeq"
    OTHER = 'Other (specify in "Comments")'


class Primer(StrEnum):
    ILLUMINA = "Illumina Artic V3"
    NANOPORE = "Nanopore Midnight V1"


class Region(StrEnum):
    STOCKHOLM = "Stockholm"
    UPPSALA = "Uppsala"
    SORMLAND = "Sörmland"
    OSTERGOTLAND = "Östergötland"
    JONKOPINGS_LAN = "Jönköpings län"
    KRONOBERG = "Kronoberg"
    KALMAR_LAN = "Kalmar län"
    GOTLAND = "Gotland"
    BLEKINGE = "Blekinge"
    SKANE = "Skåne"
    HALLAND = "Halland"
    VASTRA_GOTALANDSREGIONEN = "Västra Götalandsregionen"
    VARMLAND = "Värmland"
    OREBRO_LAN = "Örebro län"
    VASTMANLAND = "Västmanland"
    DALARNA = "Dalarna"
    GAVLEBORG = "Gävleborg"
    VASTERNORRLAND = "Västernorrland"
    JAMTLAND_HARJEDALEN = "Jämtland Härjedalen"
    VASTERBOTTEN = "Västerbotten"
    NORRBOTTEN = "Norrbotten"


class SelectionCriteria(StrEnum):
    ALLMAN_OVERVAKNING = "Allmän övervakning"
    ALLMAN_OVERVAKNING_OPPENVARD = "Allmän övervakning öppenvård"
    ALLMAN_OVERVAKNING_SLUTENVARD = "Allmän övervakning slutenvård"
    UTLANDSVISTELSE = "Utlandsvistelse"
    RIKTAD_INSAMLING = "Riktad insamling"
    UTBROTT = "Utbrott"
    VACCINATIONSGENOMBROTT = "Vaccinationsgenombrott"
    REINFEKTION = "Reinfektion"
    INFORMATION_SAKNAS = "Information saknas"


class OriginalLab(StrEnum):
    UNILABS_STOCKHOLM = "Unilabs Stockholm"
    UNILABS_ESKILSTUNA_LABORATORIUM = "Unilabs Eskilstuna Laboratorium"
    NORRLAND_UNIVERSITY_HOSPITAL = "Norrland University Hospital"
    LANSSJUKHUSET_SUNDSVALL = "Länssjukhuset Sundsvall"
    A05_DIAGNOSTICS = "A05 Diagnostics"
    SYNLAB_MEDILAB = "Synlab Medilab"
    KAROLINSKA_UNIVERSITY_HOSPITAL_SOLNA = "Karolinska University Hospital Solna"
    KAROLINSKA_UNIVERSITY_HOSPITAL_HUDDINGE = "Karolinska University Hospital Huddinge"
    LABORATORIEMEDICINSKT_CENTRUM_GOTLAND = "LaboratorieMedicinskt Centrum Gotland"
