"""Tests for the transfer of external data"""
import logging
from pathlib import Path
from typing import List

from cg.constants.constants import CaseActions
from cg.meta.external_data import ExternalDataHandler
from tests.cli.workflow.conftest import dna_case
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.store.conftest import fixture_sample_obj

from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.utils.checksum.checksum import check_md5sum, extract_md5sum


def test_add_sample_to_hk(
    external_data_handler, housekeeper_api, sample_obj, external_data_directory
):
    # GIVEN a sample_folder with associated
    external_data_directory.iterdir()


# def test_add_transfer_to_housekeeper(
#     case_id,
#     external_data_api: ExternalDataAPI,
#     fastq_file: Path,
#     mocker,
#     ticket: str,
# ):
#     """Test adding samples from a case to Housekeeper"""
#     # GIVEN a Store with a DNA case, which is available for analysis
#     cases = external_data_api.status_db.query(models.Family).filter(
#         models.Family.internal_id == case_id
#     )
#     mocker.patch.object(Store, "get_cases_from_ticket")
#     Store.get_cases_from_ticket.return_value = cases
#     samples = [fam_sample.sample for fam_sample in cases.all()[0].links]
#
#     # GIVEN a list of paths and only two samples being available
#     mocker.patch.object(ExternalDataAPI, "get_all_paths")
#     ExternalDataAPI.get_all_paths.return_value = [fastq_file]
#
#     mocker.patch.object(MockHousekeeperAPI, "last_version")
#     MockHousekeeperAPI.last_version.return_value = None
#
#     mocker.patch.object(MockHousekeeperAPI, "get_files")
#     MockHousekeeperAPI.get_files.return_value = []
#
#     mocker.patch.object(Path, "iterdir")
#     Path.iterdir.return_value = []
#
#     mocker.patch.object(ExternalDataAPI, "get_available_samples")
#     ExternalDataAPI.get_available_samples.return_value = samples[:-1]
#
#     mocker.patch.object(Store, "cases")
#     Store.cases.return_value = [{"internal_id": "yellowhog"}]
#
#     mocker.patch.object(Store, "set_case_action")
#     Store.set_case_action.return_value = None
#
#     # THEN none of the samples should exist in housekeeper
#     assert all(
#         external_data_api.housekeeper_api.bundle(sample.internal_id) is None for sample in samples
#     )
#
#     # WHEN the sample bundles are added to housekeeper
#     external_data_api.add_transfer_to_housekeeper(ticket=ticket)
#
#     # THEN two sample bundles exist in housekeeper and the file has been added to those bundles bundles
#     added_samples = list(external_data_api.housekeeper_api.bundles())
#     assert all(
#         sample.internal_id in [added_sample.name for added_sample in added_samples]
#         for sample in samples[:-1]
#     )
#     assert all(
#         sample.versions[0].files[0].path == str(fastq_file.absolute()) for sample in added_samples
#     )
#     # Then the sample that is not available should not exists
#     assert samples[-1].internal_id not in [added_sample.name for added_sample in added_samples]
#
#
# def test_get_available_samples(
#     analysis_store_trio,
#     customer_id: str,
#     external_data_api: ExternalDataAPI,
#     sample_obj: models.Sample,
#     ticket: str,
#     tmpdir_factory,
# ):
#     # GIVEN one such sample exists
#     tmp_dir_path: Path = Path(tmpdir_factory.mktemp(sample_obj.internal_id, numbered=False)).parent
#     available_samples = external_data_api.get_available_samples(folder=tmp_dir_path, ticket=ticket)
#     # THEN the function should return a list containing the sample object
#     assert available_samples == [sample_obj]
#
#
# def test_curate_sample_folder(
#     case_id, customer_id, dna_case, external_data_api: ExternalDataAPI, tmpdir_factory
# ):
#     cases = external_data_api.status_db.query(models.Family).filter(
#         models.Family.internal_id == case_id
#     )
#     sample: models.Sample = cases.first().links[0].sample
#     tmp_folder = Path(tmpdir_factory.mktemp(sample.name, numbered=False))
#     external_data_api.curate_sample_folder(
#         cust_name=customer_id, sample_folder=tmp_folder, force=False
#     )
#     assert (tmp_folder.parent / sample.internal_id).exists()
#     assert not tmp_folder.exists()
#
#
# def test_get_available_samples_no_samples_avail(
#     analysis_store_trio,
#     customer_id: str,
#     external_data_api: ExternalDataAPI,
#     ticket: str,
#     tmpdir_factory,
# ):
#     # GIVEN that the empty directory created does not contain any correct folders
#     tmp_dir_path: Path = Path(tmpdir_factory.mktemp("not_sample_id", numbered=False))
#     available_samples = external_data_api.get_available_samples(folder=tmp_dir_path, ticket=ticket)
#     # THEN the function should return an empty list
#     assert available_samples == []
#
#
# def test_checksum(fastq_file: Path):
#     """Tests if the function correctly calculates md5sum and returns the correct result."""
#     # GIVEN a fastq file with corresponding correct md5 file and a fastq file with a corresponding incorrect md5 file
#     bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")
#
#     # THEN a file with a correct md5 sum should return true
#     assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")
#
#     # THEN a file with an incorrect md5 sum should return false
#     assert not check_md5sum(
#         file_path=bad_md5sum_file_path, md5sum="c690b0124173772ec4cbbc43709d84ee"
#     )
#
#
# def test_extract_checksum(fastq_file: Path):
#     """Tests if the function successfully extract the correct md5sum."""
#
#     # Given a file containing a md5sum
#     md5sum_file = Path(f"{fastq_file.as_posix()}.md5")
#
#     # Then the function should extract it
#     assert extract_md5sum(md5sum_file=md5sum_file) == "a95cbb265540a2261fce941059784fd1"
