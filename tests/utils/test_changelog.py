from cg.utils.changelog import GitCommit
from cg.utils.changelog import build_releases
from cg.utils.changelog import cleanup_title
from cg.utils.changelog import extract_release_entries
from cg.utils.changelog import extract_entry_title
from cg.utils.changelog import filter_releases
from cg.utils.changelog import find_existing_changelog_boundary
from cg.utils.changelog import merge_generated_releases_into_changelog
from cg.utils.changelog import ReleaseEntry
from cg.utils.changelog import render_changelog


def test_cleanup_title_keeps_pull_request_number_when_requested():
    assert (
        cleanup_title("Forward auth token (#4976)(patch)", preserve_pull_request_reference=True)
        == "Forward auth token (#4976)"
    )


def test_cleanup_title_removes_pull_request_number_and_release_hint_by_default():
    assert cleanup_title("Forward auth token (#4976)(patch)") == "Forward auth token"


def test_extract_entry_title_uses_pull_request_body_when_available():
    commit = GitCommit(
        sha="abc123",
        date="2026-04-16",
        subject="Merge pull request #269 from Clinical-Genomics/add_analysis_link_balsamic_fastqs",
        body="Add analysis link balsamic fastqs",
    )

    assert extract_entry_title(commit) == "Add analysis link balsamic fastqs (#269)"


def test_extract_entry_title_falls_back_to_branch_name_for_low_signal_merge_bodies():
    commit = GitCommit(
        sha="abc123",
        date="2019-01-01",
        subject="Merge pull request #266 from Clinical-Genomics/tests-pytest-flask",
        body="reviewed by ingkebil",
    )

    assert extract_entry_title(commit) == "Tests pytest flask (#266)"


def test_extract_release_entries_prefers_structured_body_sections():
    commit = GitCommit(
        sha="abc123",
        date="2026-04-17",
        subject="Changes for running NIPT on NovaSeqX (#5009) (minor)",
        body="""## Description

This PR collects the changes needed for running NIPT on NovaSeqX.

### Added

- Data set parameter parsed from the statina section of CGConfig. Used when uploading to statina.

### Changed

- Removed the external ref flag from Fluffy start and run
- Added batch ref flag to Fluffy start and run
""",
    )

    assert extract_release_entries(commit) == [
        ReleaseEntry(
            title="Data set parameter parsed from the statina section of CGConfig. Used when uploading to statina. (#5009)",
            category="Added",
        ),
        ReleaseEntry(
            title="Removed the external ref flag from Fluffy start and run (#5009)",
            category="Changed",
        ),
        ReleaseEntry(
            title="Added batch ref flag to Fluffy start and run (#5009)",
            category="Changed",
        ),
    ]


def test_build_releases_groups_entries_until_the_next_bump_commit():
    commits = [
        GitCommit(
            sha="1111111",
            date="2026-04-16",
            subject="Add endpoint for updating lims status (#5030) (minor)",
            body="",
        ),
        GitCommit(
            sha="2222222",
            date="2026-04-16",
            subject="Bump version: 85.3.3 → 85.4.0 [skip ci]",
            body="",
        ),
        GitCommit(
            sha="3333333",
            date="2026-04-16",
            subject="Fix the tests and coverage badge (patch)",
            body="",
        ),
        GitCommit(
            sha="4444444",
            date="2026-04-16",
            subject="Bump version: 85.4.0 → 85.4.1 [skip ci]",
            body="",
        ),
    ]

    releases = build_releases(commits)

    assert [release.version for release in releases] == ["85.4.0", "85.4.1"]
    assert releases[0].entries[0].title == "Add endpoint for updating lims status (#5030)"
    assert releases[0].entries[0].category == "Added"
    assert releases[1].entries[0].title == "Fix the tests and coverage badge"
    assert releases[1].entries[0].category == "Fixed"


def test_build_releases_uses_multiple_body_entries_when_available():
    commits = [
        GitCommit(
            sha="1111111",
            date="2026-04-16",
            subject="Add input amount to all orders sample metadata for delivery report (#5011) (minor)",
            body="""## Description

### Added

- Method `get_input_amount` in the LIMS API that return the latest input amount for a DNA sample
- Input amount step names and udf keys in constants

### Changed

- order of columns in the "provberedning" section of the delivery report
""",
        ),
        GitCommit(
            sha="2222222",
            date="2026-04-16",
            subject="Bump version: 85.4.1 → 85.5.0 [skip ci]",
            body="",
        ),
    ]

    releases = build_releases(commits)

    assert [entry.title for entry in releases[0].entries] == [
        "Method `get_input_amount` in the LIMS API that return the latest input amount for a DNA sample (#5011)",
        "Input amount step names and udf keys in constants (#5011)",
        'Order of columns in the "provberedning" section of the delivery report (#5011)',
    ]
    assert [entry.category for entry in releases[0].entries] == ["Added", "Added", "Changed"]


def test_filter_releases_keeps_versions_newer_than_requested_boundary():
    releases = build_releases(
        [
            GitCommit(
                sha="1111111",
                date="2026-04-14",
                subject="Upload raw data in main upload command (#4965) (minor)",
                body="",
            ),
            GitCommit(
                sha="2222222",
                date="2026-04-14",
                subject="Bump version: 85.2.2 → 85.3.0 [skip ci]",
                body="",
            ),
            GitCommit(
                sha="3333333",
                date="2026-04-15",
                subject="Add lims_status to Sample table (#5023) (patch)",
                body="",
            ),
            GitCommit(
                sha="4444444",
                date="2026-04-15",
                subject="Bump version: 85.3.0 → 85.3.1 [skip ci]",
                body="",
            ),
        ]
    )

    filtered_releases = filter_releases(releases, after_version="85.3.0")

    assert [release.version for release in filtered_releases] == ["85.3.1"]


def test_render_changelog_outputs_keep_a_changelog_style_sections():
    releases = build_releases(
        [
            GitCommit(
                sha="1111111",
                date="2026-04-17",
                subject="Fix #5028 and a few similar ones by adding an extra trailing newline (#5029)",
                body="",
            ),
            GitCommit(
                sha="2222222",
                date="2026-04-17",
                subject="Bump version: 85.6.0 → 85.6.1 [skip ci]",
                body="",
            ),
        ]
    )

    changelog = render_changelog(releases, include_header=False)

    assert "## [85.6.1] - 2026-04-17" in changelog
    assert "### Fixed" in changelog
    assert "- Fix #5028 and a few similar ones by adding an extra trailing newline (#5029)" in changelog


def test_find_existing_changelog_boundary_skips_placeholder_versions():
    boundary = find_existing_changelog_boundary(
        """# Change Log

## [x.x.x]
### Added

## [22.26.0]
### Added
- Existing entry
"""
    )

    assert boundary.version == "22.26.0"
    assert boundary.index > 0


def test_merge_generated_releases_into_changelog_inserts_above_existing_history():
    existing_content = """# Change Log

## [x.x.x]
### Added

## [22.26.0]
### Added
- Existing entry
"""
    generated_release_block = """## [85.6.1] - 2026-04-17
### Fixed
- Generated entry (#5029)
"""

    merged_content = merge_generated_releases_into_changelog(
        existing_content=existing_content,
        generated_release_block=generated_release_block,
    )

    assert "## [85.6.1] - 2026-04-17" in merged_content
    assert merged_content.index("## [85.6.1] - 2026-04-17") < merged_content.index("## [22.26.0]")
    assert "## [x.x.x]" in merged_content
