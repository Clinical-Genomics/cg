""" Base module for building MIP bundles for linking in Housekeeper"""
import datetime as dt

from cg.exc import AnalysisDuplicationError, BundleAlreadyAddedError


def add_new_analysis(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""
    pipeline = case_obj.links[0].sample.data_analysis
    pipeline = pipeline if pipeline else "mip-rna"

    if status.analysis(family=case_obj, started_at=version_obj.created_at):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {case_obj.internal_id} {version_obj.created_at}"
        )

    new_analysis = status.add_analysis(
        pipeline=pipeline,
        version=bundle_data["pipeline_version"],
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(case_obj.analyses) == 0),
    )
    new_analysis.family = case_obj
    return new_analysis


def include_files_in_housekeeper(bundle_obj, hk_api, version_obj):
    """Function to include files in housekeeper"""
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)


def get_case(bundle_obj, status):
    """ Get a case from the status database """
    case_obj = status.family(bundle_obj.name)
    return case_obj


def reset_case_action(case_obj):
    """ Resets action on case """
    case_obj.action = None


def add_bundle(hk_api, bundle):
    """ Adds bundle to Housekeeper, raises an exception if it is already present. """

    results = hk_api.add_bundle(bundle)
    if results is None:
        raise BundleAlreadyAddedError("bundle already added")

    return results
