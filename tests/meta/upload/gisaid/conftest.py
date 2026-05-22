import pytest


@pytest.fixture
def completion_file_original_contents():
    return """provnummer,urvalskriterium,GISAID_accession
85CS900121,Allmän övervakning, EPI_ISL_75698657
85CS900136,Allmän övervakning, EPI_ISL_75698658
85CS900117,Allmän övervakning, EPI_ISL_75698659
85CS900135,Allmän övervakning, EPI_ISL_75698660
85CS900145,Allmän övervakning, EPI_ISL_75698661
85CS900145,Allmän övervakning, EPI_ISL_75698661
85AB900145,Allmän övervakning, EPI_ISL_75698669

"""


@pytest.fixture
def gisaid_log_contents():
    return """[
    {
        "code": "epi_isl_id",
        "msg": "hCoV-19/Sweden/04_SE100_85CS900121/2026; EPI_ISL_20431427"
    },
    {
        "code": "epi_isl_id",
        "msg": "hCoV-19/Sweden/04_SE100_85CS900136/2026; EPI_ISL_20431428"
    },
    {
        "code": "epi_isl_id",
        "msg": "hCoV-19/Sweden/04_SE100_85CS900117/2026; EPI_ISL_20431429"
    },
    {
        "code": "epi_isl_id",
        "msg": "hCoV-19/Sweden/24_SE100_85CS900135/2026; EPI_ISL_20431430"
    },
    {
        "code": "epi_isl_id",
        "msg": "hCoV-19/Sweden/04_SE100_85CS900145/2026; EPI_ISL_20431431"
    },
    {
        "code": "upload_count",
        "msg": "submissions uploaded: 35"
    },
    {
        "code": "failed_count",
        "msg": "submissions failed: 0"
    }
]
"""
