"""
    Tests for GisaidAPI
"""
from pathlib import Path
from typing import List

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.exc import InvalidFastaError, HousekeeperVersionMissingError
from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import FastaFile, GisaidSample
from housekeeper.store.models import File


# def test_get_gisaid_fasta_objects_no_fasta(gisaid_api, dummy_gisaid_sample, mocker):
#    # GIVEN a hk api and a dummy gisaid sample with family_id, not represented in the hk api
#    mocker.patch.object(HousekeeperAPI, "last_version")
#    HousekeeperAPI.last_version.return_value = None
#
#    # WHEN running get_gisaid_fasta
#    # THEN HousekeeperVersionMissingError is being raised
#    with pytest.raises(HousekeeperVersionMissingError):
#        gisaid_api.get_gisaid_fasta(gisaid_samples=[dummy_gisaid_sample], case_id="dummy_case")
#
#
# def test_build_gisaid_fasta_invalid_fasta(
#    gisaid_api: GisaidAPI,
#    four_gisaid_samples: List[GisaidSample],
#    invalid_fasta_file,
#    temp_result_file: Path,
#    gisaid_case_id: str,
#    mocker,
# ):
#    # GIVEN four gisaid samples and a hk api populated with a bundle with a consensus file related to the samples
#    mocker.patch.object(HousekeeperAPI, "find_file_in_latest_version")
#    HousekeeperAPI.find_file_in_latest_version.return_value = File(
#        path=invalid_fasta_file.absolute()
#    )
#
#    # WHEN running build_gisaid_fasta with the four gisaid samples
#
#    with pytest.raises(InvalidFastaError):
#        fasta_file: Path = gisaid_api.build_gisaid_fasta(
#            gisaid_samples=four_gisaid_samples, case_id=gisaid_case_id, file_name=temp_result_file
#        )
#
#
# def test_build_gisaid_fasta(
#    gisaid_api: GisaidAPI,
#    four_gisaid_samples: List[GisaidSample],
#    valid_gisiad_fasta_file,
#    valid_housekeeper_fasta_file,
#    temp_result_file: Path,
#    gisaid_case_id: str,
#    mocker,
# ):
#    # GIVEN four gisaid samples and a hk api populated with a bundle with a consensus file related to the samples
#    mocker.patch.object(HousekeeperAPI, "find_file_in_latest_version")
#    HousekeeperAPI.find_file_in_latest_version.return_value = File(
#        path=valid_housekeeper_fasta_file.absolute()
#    )
#
#    # WHEN running build_gisaid_fasta with the four gisaid samples
#    fasta_file: Path = gisaid_api.build_gisaid_fasta(
#        gisaid_samples=four_gisaid_samples, case_id=gisaid_case_id, file_name=temp_result_file
#    )
#
#    # THEN files were found and parsed into four fasta file objects
#    assert fasta_file.read_text() == valid_gisiad_fasta_file.read_text()
#
#
# def test_get_gisaid_samples(gisaid_api: GisaidAPI, case_id: str, mocker):
#    # GIVEN a gisaid_api with a Store populated with sequenced samples with family_id=case_id
#    mocker.patch.object(LimsAPI, "get_sample_attribute")
#    LimsAPI.get_sample_attribute.side_effect = 30 * [
#        "2020-11-22",
#        "Stockholm",
#        "01",
#        "Karolinska University Hospital",
#        "171 76 Stockholm, Sweden",
#    ]
#
#    # WHEN running get_gisaid_samples
#    gisaid_samples = gisaid_api.get_gisaid_samples(case_id=case_id)
#
#    # THEN assert
#    assert gisaid_samples != []
#    for sample in gisaid_samples:
#        assert isinstance(sample, GisaidSample)
#
#
# def test_get_gisaid_samples_no_samples(gisaid_api):
#    # GIVEN a
#
#    # WHEN running get_gisaid_samples
#    gisaid_samples: GisaidAPI = gisaid_api.get_gisaid_samples(case_id="dummy_case")
#
#    # THEN assert
#    assert gisaid_samples == []
#
#
# def test_build_gisaid_csv(
#    gisaid_api, four_gisaid_samples, four_samples_csv, temp_result_file: Path
# ):
#    # GIVEN four gisaid samples
#
#    # WHEN running build_gisaid_csv
#    gisaid_api.build_gisaid_csv(gisaid_samples=four_gisaid_samples, file_name=temp_result_file)
#
#    # THEN the generated file should have the expected content
#    assert temp_result_file.read_text() == four_samples_csv
#
