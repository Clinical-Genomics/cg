"""
    Tests for GisaidAPI
"""
from pathlib import Path
from typing import List

from cg.exc import FastaSequenceMissingError
import pytest

from cg.meta.upload.gisaid.models import GisaidSample


def test_get_fasta_sequence(valid_fasta_file, gisaid_api):
    # GIVEN a valid consencus fasta file

    # WHEN running get_fasta_sequence
    sequence = gisaid_api.get_fasta_sequence(fastq_path=valid_fasta_file)

    # THEN assert the returned sequence is the second line in the file
    with open(valid_fasta_file) as handle:
        fasta_lines = handle.readlines()
        assert sequence == fasta_lines[1].rstrip("\n")


def test_get_fasta_sequence_invalid_file(invalid_fasta_file, gisaid_api):
    # GIVEN a valid consencus fasta file

    # WHEN running get_fasta_sequence
    # THEN FastaSequenceMissingError is raised
    with pytest.raises(FastaSequenceMissingError):
        gisaid_api.get_fasta_sequence(fastq_path=invalid_fasta_file)


def test_get_gisaid_samples(gisaid_api):
    # GIVEN a
    family_id = "gisaid_family_id"

    # WHEN running get_gsaid_samples
    gisaid_samples = gisaid_api.get_gsaid_samples(family_id=family_id)

    # THEN assert
    assert gisaid_samples != []
    for sample in gisaid_samples:
        assert isinstance(sample, GisaidSample)


def test_get_gisaid_samples_no_samples(gisaid_api):
    # GIVEN a
    family_id = "family_not_in_db_id"

    # WHEN running get_gsaid_samples
    gisaid_samples = gisaid_api.get_gsaid_samples(family_id=family_id)

    # THEN assert
    assert gisaid_samples == []


def test_build_gisaid_csv(gisaid_api, four_gisaid_samples, four_samples_csv):

    file_name = "test.csv"
    file = Path(file_name)
    gisaid_api.build_gisaid_csv(gsaid_samples=four_gisaid_samples, file_name=file_name)
    assert file.read_text() == four_samples_csv
    file.unlink()
