from typing import Optional, List
from cg.store import Store
from cg.store.models import Application, ApplicationVersion


def test_get_current_application_version_by_tag_existing_tag(base_store: Store):
    """Test that giving an existing tag returns the correct application version."""
    # GIVEN an application in store with a valid tag
    application: Application = base_store.get_applications()[0]
    tag: str = application.tag
    assert tag

    # WHEN getting the current application version by tag
    application_version: ApplicationVersion = base_store.get_current_application_version_by_tag(
        tag=tag
    )

    # THEN the application version has the same application tag as the application
    assert application_version.application.tag == application.tag


def test_get_current_application_version_by_tag_invalid_tag(
    base_store: Store,
    invalid_application_tag: str,
):
    """Test that giving an invalid tag returns None."""
    # GIVEN a store with applications and an invalid tag
    applications: List[Application] = base_store.get_applications()
    tags: List[str] = [application.tag for application in applications]
    assert invalid_application_tag not in tags

    # WHEN getting the current application version by tag
    application_version: Optional[
        ApplicationVersion
    ] = base_store.get_current_application_version_by_tag(tag=invalid_application_tag)

    # THEN the application version is None
    assert application_version is None


def test_get_current_application_version_by_tag_latest_version(
    store_with_different_application_versions: Store,
):
    """Test that the returned application version is the most recent."""
    # GIVEN a store with applications versions with different 'valid_from' attributes
    application_versions: List[
        ApplicationVersion
    ] = store_with_different_application_versions._get_query(table=ApplicationVersion).all()
    assert application_versions[0].valid_from != application_versions[-1].valid_from

    # GIVEN a valid application tag
    tag: str = store_with_different_application_versions.get_applications()[0].tag
    application_versions_with_tag: List[ApplicationVersion] = [
        app_ver for app_ver in application_versions if app_ver.application.tag == tag
    ]
    assert len(application_versions_with_tag) > 0

    # WHEN getting the current application version given a tag
    current_application_version: ApplicationVersion = (
        store_with_different_application_versions.get_current_application_version_by_tag(tag=tag)
    )

    # THEN the application version has the newest attribute 'valid_from'
    for app_version in application_versions_with_tag:
        assert current_application_version.valid_from >= app_version.valid_from
