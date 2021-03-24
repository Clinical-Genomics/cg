from cg.apps.demultiplex.novaseq_sample_sheet import SampleSheet


def test_convert_to_sheet(novaseq_sample_sheet_object: SampleSheet):
    # GIVEN a sample sheet object populated with samples
    assert novaseq_sample_sheet_object.lims_samples

    # WHEN converting to sample sheet
    sample_sheet_string: str = novaseq_sample_sheet_object.convert_to_sample_sheet()

    # THEN assert a correctly formated sample sheet was created
    print(sample_sheet_string)
    assert 0
