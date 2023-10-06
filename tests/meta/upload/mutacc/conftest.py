import pytest

from cg.apps.scout.scout_export import ScoutExportCase
from cg.constants.pedigree import Pedigree
from cg.constants.subject import PlinkGender, PlinkPhenotypeStatus, RelationshipStatus
from cg.meta.upload.mutacc import UploadToMutaccAPI


class MockMutaccAuto:
    """Mock class for mutacc_auto api"""

    @staticmethod
    def extract_reads(*args, **kwargs):
        """mock extract_reads method"""
        _, _ = args, kwargs

    @staticmethod
    def import_reads(*args, **kwargs):
        """mock import_reads method"""
        _, _ = args, kwargs


class MockScoutApi:
    """Mock class for Scout api"""

    @staticmethod
    def get_causative_variants(case_id):
        """mock get_causative_variants"""
        _ = case_id
        return []

    @property
    def client(self):
        """Client URI"""
        return "mongodb://"

    @property
    def name(self):
        """Name property"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @name.deleter
    def name(self):
        del self._name


@pytest.fixture(name="scout_export_case_data")
def scout_export_case_data(customer_id: str) -> dict:
    """Return information in the form of a scout export case"""
    case_data = {
        "_id": "internal_id",
        "owner": customer_id,
        "analysis_date": "2020-11-18T15:02:03.554000",
        "causatives": ["variant_id"],
        "individuals": [
            {
                "individual_id": "individual_1",
                "bam_file": "",
                Pedigree.SEX: PlinkGender.MALE,
                Pedigree.FATHER: "individual_2",
                Pedigree.MOTHER: "individual_3",
                Pedigree.PHENOTYPE: PlinkPhenotypeStatus.AFFECTED,
            },
            {
                "individual_id": "individual_2",
                "bam_file": "",
                Pedigree.SEX: PlinkGender.MALE,
                Pedigree.FATHER: RelationshipStatus.HAS_NO_PARENT,
                Pedigree.MOTHER: RelationshipStatus.HAS_NO_PARENT,
                Pedigree.PHENOTYPE: PlinkPhenotypeStatus.UNAFFECTED,
            },
            {
                "individual_id": "individual_3",
                "bam_file": "",
                Pedigree.SEX: PlinkGender.FEMALE,
                Pedigree.FATHER: RelationshipStatus.HAS_NO_PARENT,
                Pedigree.MOTHER: RelationshipStatus.HAS_NO_PARENT,
                Pedigree.PHENOTYPE: PlinkPhenotypeStatus.UNAFFECTED,
            },
        ],
    }
    return case_data


@pytest.fixture(name="scout_export_case")
def scout_export_case(scout_export_case_data: dict) -> ScoutExportCase:
    """Returns a export case object"""

    return ScoutExportCase.model_validate(scout_export_case_data)


@pytest.fixture(name="scout_export_case_missing_bam")
def scout_export_case_missing_bam(scout_export_case_data: dict) -> ScoutExportCase:
    """Returns a export case object where one individual is missing bam file"""
    scout_export_case_data["individuals"][1].pop("bam_file")

    return ScoutExportCase.model_validate(scout_export_case_data)


@pytest.fixture(name="scout_export_case_no_causatives")
def scout_export_case_no_causatives(scout_export_case_data: dict) -> ScoutExportCase:
    """Returns a export case object without causatives"""
    scout_export_case_data.pop("causatives")

    return ScoutExportCase.model_validate(scout_export_case_data)


@pytest.fixture(scope="function")
def mutacc_upload_api():
    """
    Fixture for a mutacc upload api
    """

    scout_api = MockScoutApi()
    mutacc_auto_api = MockMutaccAuto()

    _api = UploadToMutaccAPI(scout_api=scout_api, mutacc_auto_api=mutacc_auto_api)

    return _api
