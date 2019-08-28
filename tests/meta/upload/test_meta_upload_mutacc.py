""" Tests for cg.meta.upload.mutacc module """

import os

from cg.meta.upload.mutacc import UploadToMutaccAPI


def test_instatiate():
    """
        Test instatiate object of type UploadToMutaccAPI
    """
    # GIVEN a scout-api and mutacc-auto-api

    mutacc_auto_api = 1
    scou_api = 1

    # When instatiating the mutacc_upload api
    mutacc_upload_api = UploadToMutaccAPI(scou_api, mutacc_auto_api)

    # THEN all attributes should have been set
    assert mutacc_upload_api.scout == scou_api
    assert mutacc_upload_api.mutacc_auto == mutacc_auto_api


def test_data(mutacc_upload_api, mocker):
    """
        Test the data method
    """
    # GIVEN a case dictionary
    case = {
        '_id': 'internal_id',
        'causatives': ['variant_id'],
        'individuals': [{'individual_id': 'individual_1',
                         'bam_file': ''},
                        {'individual_id': 'individual_2',
                         'bam_file': ''},
                        {'individual_id': 'individual_3',
                         'bam_file': ''}]
    }

    mocker.patch.object(os.path, 'isfile')
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should have keys 'case', and 'causatives'
    assert set(result.keys()) == {'case', 'causatives'}


def test_data_no_bam(mutacc_upload_api, mocker):
    """
        Test get data when no bam_file field is given for one of the samples
    """

    # GIVEN a case dictionary where one individual is missing bam_file
    case = {
        '_id': 'internal_id',
        'causatives': ['variant_id'],
        'individuals': [{'individual_id': 'individual_1',
                         'bam_file': ''},
                        {'individual_id': 'individual_2'},
                        {'individual_id': 'individual_3',
                         'bam_file': ''}]
    }

    # mock that file is a file
    mocker.patch.object(os.path, 'isfile')
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}


def test_data_bam_path_not_exists(mutacc_upload_api, mocker):
    """
        Test get data when bam file does not exist
    """
    # GIVEN a case dictionary
    case = {
        '_id': 'internal_id',
        'causatives': ['variant_id'],
        'individuals': [{'individual_id': 'individual_1',
                         'bam_file': ''},
                        {'individual_id': 'individual_2',
                         'bam_file': ''},
                        {'individual_id': 'individual_3',
                         'bam_file': ''}]
    }

    # mock that file is not a file
    mocker.patch.object(os.path, 'isfile')
    os.path.isfile.return_value = False

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}


def test_data_no_causatives(mutacc_upload_api, mocker):
    """
        Test get data when no causatives are given
    """
    # GIVEN a case dictionary with no causative variants
    case = {
        '_id': 'internal_id',
        'individuals': [{'individual_id': 'individual_1',
                         'bam_file': ''},
                        {'individual_id': 'individual_2',
                         'bam_file': ''},
                        {'individual_id': 'individual_3',
                         'bam_file': ''}]
    }

    mocker.patch.object(os.path, 'isfile')
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}
