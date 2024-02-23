""" Tests for cg.meta.upload.mutacc module """

import os

from cg.apps.scout.scout_export import ScoutExportCase
from cg.meta.upload.mutacc import (
    UploadToMutaccAPI,
    resolve_parent,
    resolve_phenotype,
    resolve_sex,
)


def test_instantiate():
    """
    Test instantiate object of type UploadToMutaccAPI
    """
    # GIVEN a scout-api and mutacc-auto-api

    mutacc_auto_api = 1
    scout_api = 1

    # When instatiating the mutacc_upload api
    mutacc_upload_api = UploadToMutaccAPI(scout_api, mutacc_auto_api)

    # THEN all attributes should have been set
    assert mutacc_upload_api.scout == scout_api
    assert mutacc_upload_api.mutacc_auto == mutacc_auto_api


def test_data(mutacc_upload_api, scout_export_case: ScoutExportCase, mocker):
    """
    Test the data method
    """
    # GIVEN a case object

    mocker.patch.object(os.path, "isfile")
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(scout_export_case)

    # THEN data dict should have keys 'case', and 'causatives'
    assert set(result.keys()) == {"case", "causatives"}


def test_data_no_bam(mutacc_upload_api, scout_export_case_missing_bam: ScoutExportCase, mocker):
    """
    Test get data when no bam_file field is given for one of the samples
    """

    # GIVEN a case dictionary where one individual is missing bam_file
    case = scout_export_case_missing_bam

    # mock that file is a file
    mocker.patch.object(os.path, "isfile")
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}


def test_data_bam_path_not_exists(mutacc_upload_api, scout_export_case: ScoutExportCase, mocker):
    """
    Test get data when bam file does not exist
    """
    # GIVEN a case object
    case = scout_export_case

    # mock that file is not a file
    mocker.patch.object(os.path, "isfile")
    os.path.isfile.return_value = False

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}


def test_data_no_causatives(
    mutacc_upload_api, scout_export_case_no_causatives: ScoutExportCase, mocker
):
    """
    Test get data when no causatives are given
    """
    # GIVEN a case dictionary with no causative variants
    case = scout_export_case_no_causatives

    mocker.patch.object(os.path, "isfile")
    os.path.isfile.return_value = True

    # WHEN generating data
    result = mutacc_upload_api.data(case)

    # THEN data dict should be empty
    assert result == {}


def test_resolve_sex():
    """test resolve_sex"""
    # GIVEN scout sex codes
    scout_male = "1"
    scout_female = "2"
    scout_unknown = "0"

    # WHEN converting to mutacc sex codes with resolve_sex
    mutacc_male = resolve_sex(scout_male)
    mutacc_female = resolve_sex(scout_female)
    mutacc_unknown = resolve_sex(scout_unknown)

    # THEN the sex codes should have been converted
    assert mutacc_male == "male"
    assert mutacc_female == "female"
    assert mutacc_unknown == "unknown"


def test_resolve_parent():
    """test resolve_parent"""
    # GIVEN scout parent codes
    scout_no_parent = ""
    scout_father = "father_id"
    scout_mother = "mother_id"

    # WHEN converting to mutacc parent codes with resolve_parent
    mutacc_no_parent = resolve_parent(scout_no_parent)
    mutacc_father = resolve_parent(scout_father)
    mutacc_mother = resolve_parent(scout_mother)

    # THEN the parent codes should have been converted
    assert mutacc_no_parent == "0"
    assert mutacc_father == scout_father
    assert mutacc_mother == scout_mother


def test_resolve_phenotype():
    """test resolve_phenotype"""
    # GIVEN scout phenotype codes
    scout_affected = 2
    scout_unaffected = 1

    # WHEN converting to mutacc phenotype codes with resolve_phenotype
    mutacc_affected = resolve_phenotype(scout_affected)
    mutacc_unaffected = resolve_phenotype(scout_unaffected)

    # THEN the phenotype codes should have been converted
    assert mutacc_affected == "affected"
    assert mutacc_unaffected == "unaffected"
