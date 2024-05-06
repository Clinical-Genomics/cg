"""Test observations API methods."""

from pathlib import Path

from pytest_mock import MockFixture

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LoqusdbInstance, MipDNALoadParameters
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case


def test_get_loqusdb_api(cg_context: CGConfig, mip_dna_observations_api: MipDNAObservationsAPI):
    """Test Loqusdb API retrieval given a Loqusdb instance."""

    # GIVEN a WES Loqusdb instance and an observations API
    loqusdb_instance = LoqusdbInstance.WES

    # GIVEN the expected Loqusdb config dictionary
    loqusdb_wes_config: dict[str, Path] = cg_context.loqusdb_wes

    # WHEN calling the Loqusdb API get method
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(loqusdb_instance)

    # THEN a WES Loqusdb API should be returned
    assert isinstance(loqusdb_api, LoqusdbAPI)
    assert loqusdb_api.binary_path == loqusdb_wes_config.binary_path
    assert loqusdb_api.config_path == loqusdb_wes_config.config_path


def test_is_duplicate(
    case_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that is not in Loqusdb."""

    # GIVEN a Loqusdb instance with no case duplicates
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN there should be no duplicates in Loqusdb
    assert is_duplicate is False


def test_is_duplicate_true(
    case_id: str,
    loqusdb_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value={"case_id": case_id})

    # WHEN checking that case has not been uploaded to Loqusdb
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN an upload of a duplicate case should be detected
    assert is_duplicate is True


def test_is_duplicate_loqusdb_id(
    case_id: str,
    loqusdb_id: str,
    mip_dna_observations_api: MipDNAObservationsAPI,
    mip_dna_observations_input_files: MipDNAObservationsInputFiles,
    mocker: MockFixture,
):
    """Test duplicate extraction for a case that already exists in Loqusdb."""

    # GIVEN a Loqusdb instance with a duplicated case and whose samples already have a Loqusdb ID
    case: Case = mip_dna_observations_api.store.get_case_by_internal_id(internal_id=case_id)
    loqusdb_api: LoqusdbAPI = mip_dna_observations_api.get_loqusdb_api(LoqusdbInstance.WGS)
    case.links[0].sample.loqusdb_id = loqusdb_id
    mocker.patch.object(LoqusdbAPI, "get_case", return_value=None)
    mocker.patch.object(LoqusdbAPI, "get_duplicate", return_value=False)

    # WHEN checking that the sample observations have already been uploaded
    is_duplicate: bool = mip_dna_observations_api.is_duplicate(
        case=case,
        loqusdb_api=loqusdb_api,
        profile_vcf_path=mip_dna_observations_input_files.profile_vcf_path,
        profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
    )

    # THEN a duplicated upload should be identified
    assert is_duplicate is True
