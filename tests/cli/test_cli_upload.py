""" Test cg.cli.upload module """

from cg.cli.upload.upload import LinkHelper


def test_all_samples_are_non_tumor(analysis_store):

    family_obj = analysis_store.family('yellowhog')
    assert LinkHelper.all_samples_are_non_tumour(family_obj.links)


def test_all_samples_data_analysis(analysis_store):

    family_obj = analysis_store.family('yellowhog')
    assert LinkHelper.all_samples_data_analysis(family_obj.links, ['mip'])


def test_all_samples_are_wgs(analysis_store):

    family_obj = analysis_store.family('yellowhog')
    assert LinkHelper.all_samples_are_wgs(family_obj.links)
