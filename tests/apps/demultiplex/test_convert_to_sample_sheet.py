from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator


def test_convert_to_sheet(novaseq_sample_sheet_object: SampleSheetCreator):
    # GIVEN a sample sheet object populated with samples
    assert novaseq_sample_sheet_object.lims_samples

    # WHEN converting to sample sheet
    sample_sheet: str = novaseq_sample_sheet_object.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    print(sample_sheet)
    assert 0
