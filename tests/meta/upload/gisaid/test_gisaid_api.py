"""
    Tests for GisaidAPI
"""
from pathlib import Path
from typing import List

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import FastaSequenceMissingError, HousekeeperVersionMissingError
from cg.meta.upload.gisaid.models import FastaFile, GisaidSample
from tests.store_helpers import StoreHelpers


def test_get_fasta_sequence(valid_fasta_file, gisaid_api):
    # GIVEN a valid consensus fasta file

    # WHEN running get_fasta_sequence
    sequence = gisaid_api.get_fasta_sequence(fastq_path=valid_fasta_file)

    # THEN assert the returned sequence is the second line in the file
    with open(valid_fasta_file) as handle:
        fasta_lines = handle.readlines()
        assert sequence == fasta_lines[1].rstrip("\n")


def test_get_fasta_sequence_invalid_file(gisaid_api, invalid_fasta_file):
    # GIVEN a invalid consensus fasta file
    # WHEN running get_fasta_sequence
    # THEN FastaSequenceMissingError is raised
    with pytest.raises(FastaSequenceMissingError):
        gisaid_api.get_fasta_sequence(fastq_path=invalid_fasta_file)


def test_get_gisaid_fasta_objects(
    gisaid_api,
    four_gisaid_samples: List[GisaidSample],
    bundle_with_four_samples: dict,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
):
    # GIVEN four gisaid samples and a hk api populated with a bundle with consensus files related to the samples
    gisaid_api.housekeeper_api_ = helpers.ensure_hk_bundle(
        real_housekeeper_api, bundle_with_four_samples, include=True
    )

    # WHEN running get_gisaid_fasta_objects with the four gisaid samples
    fasta_objects: List[FastaFile] = gisaid_api.get_gisaid_fasta_objects(
        gsaid_samples=four_gisaid_samples
    )
    # THEN files were found and parsed into four fasta file objects
    assert len(fasta_objects) == 4
    for obj in fasta_objects:
        assert isinstance(obj, FastaFile)


def test_get_gisaid_fasta_objects_no_fasta(
    gisaid_api,
    real_housekeeper_api: HousekeeperAPI,
    dummy_gisaid_sample,
):
    # GIVEN a hk api and a dummy gisaid sample with family_id, not represented in the hk api
    gisaid_api.housekeeper_api_ = real_housekeeper_api

    # WHEN running get_gisaid_fasta_objects
    # THEN HousekeeperVersionMissingError is being raised
    with pytest.raises(HousekeeperVersionMissingError):
        gisaid_api.get_gisaid_fasta_objects(gsaid_samples=[dummy_gisaid_sample])


def test_build_gisaid_fasta(
    gisaid_api,
    four_gisaid_samples: List[GisaidSample],
    bundle_with_four_samples: dict,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    valid_concat_fasta_file,
    gisaid_file_name: Path,
):
    # GIVEN four gisaid samples and a hk api populated with a bundle with consensus files related to the samples
    gisaid_api.housekeeper_api_ = helpers.ensure_hk_bundle(
        real_housekeeper_api, bundle_with_four_samples, include=True
    )

    # WHEN running build_gisaid_fasta with the four gisaid samples
    gisaid_api.build_gisaid_fasta(
        gsaid_samples=four_gisaid_samples, file_name=gisaid_file_name.name
    )
    # THEN the concatenated fasta file has the expected content
    assert gisaid_file_name.read_text() == valid_concat_fasta_file


def test_get_gisaid_samples(gisaid_api, case_id):
    # GIVEN a gisaid_api with a Store populated with sequenced samples with family_id=case_id

    # WHEN running get_gisaid_samples
    gisaid_samples = gisaid_api.get_gsaid_samples(family_id=case_id)

    # THEN assert
    assert gisaid_samples != []
    for sample in gisaid_samples:
        assert isinstance(sample, GisaidSample)


def test_get_gisaid_samples_no_samples(gisaid_api):
    # GIVEN a

    # WHEN running get_gisaid_samples
    gisaid_samples = gisaid_api.get_gsaid_samples(family_id="dummy_case")

    # THEN assert
    assert gisaid_samples == []


def test_build_gisaid_csv(
    gisaid_api, four_gisaid_samples, four_samples_csv, gisaid_file_name: Path
):
    # GIVEN four gisaid samples

    # WHEN running build_gisaid_csv
    gisaid_api.build_gisaid_csv(gsaid_samples=four_gisaid_samples, file_name=gisaid_file_name)

    # THEN the generated file should have the expected content
    assert gisaid_file_name.read_text() == four_samples_csv
