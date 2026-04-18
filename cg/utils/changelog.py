from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"
DEFAULT_HEADER = """# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.0.0/)
"""

BUMP_VERSION_PATTERN = re.compile(
    r"^Bump version:\s+(?P<old>\S+)\s+(?:→|->)\s+(?P<new>\S+)(?:\s+\[skip ci\])?$"
)
MERGE_PULL_REQUEST_PATTERN = re.compile(
    r"^Merge pull request #(?P<number>\d+) from (?P<source>.+?)/(?P<branch>.+)$"
)
SECTION_HEADING_PATTERN = re.compile(r"^#{2,6}\s*(Added|Changed|Fixed)\s*$", re.IGNORECASE)
ANY_HEADING_PATTERN = re.compile(r"^#{1,6}\s+")
LIST_ITEM_PATTERN = re.compile(r"^\s*[-*]\s+(?P<text>.+)$")
CONVENTIONAL_PREFIX_PATTERN = re.compile(
    r"^(?P<prefix>feat|fix|chore|docs|refactor|style|perf|test|ci|build)"
    r"(?:\([^)]+\))?:\s*",
    re.IGNORECASE,
)
PULL_REQUEST_SUFFIX_PATTERN = re.compile(r"\s*\(#\d+\)")
INLINE_PULL_REQUEST_PATTERN = re.compile(r"\(#(?P<number>\d+)\)")
RELEASE_HINT_PATTERN = re.compile(r"\s*\((?:major|minor|patch)\)\s*$", re.IGNORECASE)
LOW_SIGNAL_PATTERNS = (
    re.compile(r"^reviewed\s+by\b", re.IGNORECASE),
    re.compile(r"request\s+for\s+changes", re.IGNORECASE),
    re.compile(r"^merge\s+branch\b", re.IGNORECASE),
    re.compile(r"^merged?\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class GitCommit:
    sha: str
    date: str
    subject: str
    body: str


@dataclass(frozen=True)
class ReleaseEntry:
    title: str
    category: str


@dataclass(frozen=True)
class Release:
    version: str
    previous_version: str
    date: str
    entries: list[ReleaseEntry]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a changelog from first-parent git history and bump-version commits."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path to inspect. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--ref",
        default="HEAD",
        help="Git revision to inspect on the first-parent history. Defaults to HEAD.",
    )
    parser.add_argument(
        "--after-version",
        help="Only include releases newer than this version.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the generated changelog to this path instead of stdout.",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Render one bullet list per release instead of Added/Changed/Fixed sections.",
    )
    parser.add_argument(
        "--skip-header",
        action="store_true",
        help="Omit the standard changelog header.",
    )
    parser.add_argument(
        "--no-unreleased",
        action="store_true",
        help="Do not include commits newer than the latest version bump in an Unreleased section.",
    )
    return parser


def get_git_commits(repo_path: Path, ref: str) -> list[GitCommit]:
    command = [
        "git",
        "log",
        "--first-parent",
        "--reverse",
        "--date=short",
        f"--pretty=format:%H{FIELD_SEPARATOR}%ad{FIELD_SEPARATOR}%s{FIELD_SEPARATOR}%b{RECORD_SEPARATOR}",
        ref,
    ]
    completed_process = subprocess.run(
        command,
        cwd=repo_path,
        capture_output=True,
        check=True,
        text=True,
    )
    records = completed_process.stdout.rstrip(RECORD_SEPARATOR).split(RECORD_SEPARATOR)
    commits: list[GitCommit] = []
    for record in records:
        if not record:
            continue
        sha, date, subject, body = record.split(FIELD_SEPARATOR, maxsplit=3)
        commits.append(GitCommit(sha=sha, date=date, subject=subject.strip(), body=body.strip()))
    return commits


def build_releases(commits: list[GitCommit], include_unreleased: bool = True) -> list[Release]:
    releases: list[Release] = []
    pending_entries: list[ReleaseEntry] = []
    unreleased_date = commits[-1].date if commits else ""

    for commit in commits:
        bump_match = BUMP_VERSION_PATTERN.match(commit.subject)
        if bump_match:
            releases.append(
                Release(
                    version=bump_match.group("new"),
                    previous_version=bump_match.group("old"),
                    date=commit.date,
                    entries=pending_entries.copy(),
                )
            )
            pending_entries = []
            continue

        if should_ignore_commit(commit):
            continue

        pending_entries.extend(extract_release_entries(commit))

    if include_unreleased and pending_entries:
        releases.append(
            Release(
                version="Unreleased",
                previous_version="",
                date=unreleased_date,
                entries=pending_entries.copy(),
            )
        )

    return releases


def should_ignore_commit(commit: GitCommit) -> bool:
    subject = commit.subject
    return subject.startswith("Merge branch 'master'") or subject.startswith(
        "Merge remote-tracking branch"
    )


def extract_entry_title(commit: GitCommit) -> str:
    merge_match = MERGE_PULL_REQUEST_PATTERN.match(commit.subject)
    if merge_match:
        candidate = pick_merge_pull_request_title(commit.body)
        if not candidate:
            candidate = humanize_branch_name(merge_match.group("branch"))
        return append_pull_request_reference(
            cleanup_title(candidate, preserve_pull_request_reference=True),
            get_pull_request_reference(commit.subject),
        )

    return cleanup_title(commit.subject, preserve_pull_request_reference=True)


def extract_release_entries(commit: GitCommit) -> list[ReleaseEntry]:
    pull_request_reference = get_pull_request_reference(commit.subject)
    body_entries = extract_structured_body_entries(commit.body, pull_request_reference)
    if body_entries:
        return body_entries

    entry_title = extract_entry_title(commit)
    if not entry_title:
        return []
    return [ReleaseEntry(title=entry_title, category=categorize_entry(entry_title))]


def pick_merge_pull_request_title(body: str) -> str:
    for line in split_nonempty_lines(body):
        if any(pattern.search(line) for pattern in LOW_SIGNAL_PATTERNS):
            continue
        return line
    return ""


def split_nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def cleanup_title(title: str, preserve_pull_request_reference: bool = False) -> str:
    cleaned_title = title.strip()
    cleaned_title = CONVENTIONAL_PREFIX_PATTERN.sub("", cleaned_title)
    if not preserve_pull_request_reference:
        cleaned_title = PULL_REQUEST_SUFFIX_PATTERN.sub("", cleaned_title)
    while True:
        updated_title = RELEASE_HINT_PATTERN.sub("", cleaned_title)
        if updated_title == cleaned_title:
            break
        cleaned_title = updated_title
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip(" -")
    return cleaned_title[:1].upper() + cleaned_title[1:] if cleaned_title else ""


def humanize_branch_name(branch_name: str) -> str:
    cleaned_branch = re.sub(r"^\d+-", "", branch_name)
    cleaned_branch = cleaned_branch.replace("_", " ").replace("-", " ").strip()
    return cleaned_branch[:1].upper() + cleaned_branch[1:] if cleaned_branch else branch_name


def get_pull_request_reference(subject: str) -> str | None:
    merge_match = MERGE_PULL_REQUEST_PATTERN.match(subject)
    if merge_match:
        return f"(#{merge_match.group('number')})"

    inline_match = INLINE_PULL_REQUEST_PATTERN.search(subject)
    if inline_match:
        return inline_match.group(0)
    return None


def append_pull_request_reference(title: str, pull_request_reference: str | None) -> str:
    if not title or not pull_request_reference or pull_request_reference in title:
        return title
    return f"{title} {pull_request_reference}"


def extract_structured_body_entries(
    body: str, pull_request_reference: str | None
) -> list[ReleaseEntry]:
    entries: list[ReleaseEntry] = []
    current_category: str | None = None
    in_code_block = False

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if line == "---------" or line.lower().startswith("co-authored-by:"):
            continue

        section_heading = SECTION_HEADING_PATTERN.match(line)
        if section_heading:
            current_category = section_heading.group(1).capitalize()
            continue
        if ANY_HEADING_PATTERN.match(line):
            current_category = None
            continue

        if not current_category:
            continue

        list_item_match = LIST_ITEM_PATTERN.match(line)
        if not list_item_match:
            continue

        title = cleanup_title(
            list_item_match.group("text"),
            preserve_pull_request_reference=True,
        )
        title = append_pull_request_reference(title, pull_request_reference)
        if title:
            entries.append(ReleaseEntry(title=title, category=current_category))

    return deduplicate_entries(entries)


def deduplicate_entries(entries: list[ReleaseEntry]) -> list[ReleaseEntry]:
    unique_entries: list[ReleaseEntry] = []
    seen_entries: set[tuple[str, str]] = set()
    for entry in entries:
        key = (entry.category, entry.title)
        if key in seen_entries:
            continue
        seen_entries.add(key)
        unique_entries.append(entry)
    return unique_entries


def categorize_entry(title: str) -> str:
    normalized_title = title.lower()
    if re.match(
        r"^(add|allow|create|enable|implement|include|introduce|mark|new|support|upload)\b",
        normalized_title,
    ):
        return "Added"
    if re.match(
        r"^(fix|avoid|correct|handle|patch|prevent|restore|revert|stop|suppress)\b",
        normalized_title,
    ):
        return "Fixed"
    return "Changed"


def filter_releases(releases: list[Release], after_version: str | None) -> list[Release]:
    if not after_version:
        return releases

    for index, release in enumerate(releases):
        if release.version == after_version:
            return releases[index + 1 :]
        if release.previous_version == after_version:
            return releases[index:]
    return releases


def render_changelog(releases: list[Release], flat: bool = False, include_header: bool = True) -> str:
    lines: list[str] = []
    if include_header:
        lines.append(DEFAULT_HEADER.strip())
        lines.append("")

    for release in reversed(releases):
        lines.extend(render_release(release, flat=flat))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_release(release: Release, flat: bool = False) -> list[str]:
    heading = f"## [{release.version}]"
    if release.version != "Unreleased" and release.date:
        heading = f"{heading} - {release.date}"

    lines = [heading]
    if not release.entries:
        return lines

    if flat:
        lines.extend(f"- {entry.title}" for entry in release.entries)
        return lines

    for category in ("Added", "Changed", "Fixed"):
        category_entries = [entry.title for entry in release.entries if entry.category == category]
        if not category_entries:
            continue
        lines.append(f"### {category}")
        lines.extend(f"- {title}" for title in category_entries)
    return lines


def main() -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args()

    commits = get_git_commits(repo_path=arguments.repo, ref=arguments.ref)
    releases = build_releases(commits=commits, include_unreleased=not arguments.no_unreleased)
    filtered_releases = filter_releases(releases=releases, after_version=arguments.after_version)
    changelog = render_changelog(
        releases=filtered_releases,
        flat=arguments.flat,
        include_header=not arguments.skip_header,
    )

    if arguments.output:
        arguments.output.write_text(changelog, encoding="utf-8")
    else:
        print(changelog, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
