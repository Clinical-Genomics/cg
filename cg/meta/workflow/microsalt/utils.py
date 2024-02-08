from datetime import datetime
import os
from pathlib import Path

from cg.exc import MissingAnalysisRunDirectory


def get_project_directory_date(dir_name: str) -> datetime:
    # Assumes format like <project_id>_year.month.day_hour.minute.second
    _, date, time = dir_name.split("_")
    date_time = f"{date}_{time}"
    return datetime.strptime(date_time, "%Y.%m.%d_%H.%M.%S")


def get_project_directories(project_id: str, directory: Path) -> list[str]:
    return [sub_dir for sub_dir in os.listdir(directory) if sub_dir.startswith(project_id)]


def sort_project_directories_by_date(project_directories: list[str]) -> list[str]:
    return sorted(project_directories, key=get_project_directory_date, reverse=True)


def get_most_recent_project_directory(project_id: str, directory: Path) -> Path:
    project_directories: list[str] = get_project_directories(
        project_id=project_id, directory=directory
    )
    sorted_project_directories: list[str] = sort_project_directories_by_date(project_directories)

    if not sorted_project_directories:
        raise MissingAnalysisRunDirectory(f"No analysis directory found for project {project_id}.")

    return Path(directory, sorted_project_directories[0])
