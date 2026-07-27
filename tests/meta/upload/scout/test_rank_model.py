import pytest
from pydantic import ValidationError

from cg.meta.upload.scout.rank_model import RankModel, parse_rank_model_file


def test_parse_rank_model_success():
    # GIVEN a valid rank model file
    file = "tests/fixtures/meta/rank_model/correct_rank_model.ini"

    # WHEN parsing the rank model file
    rank_model = parse_rank_model_file(file)

    # THEN a RankModel object with the version of teh file is returned
    assert rank_model == RankModel(path=file, version="2.5")


@pytest.mark.parametrize(
    "file",
    [
        "tests/fixtures/meta/rank_model/rank_model_no_version_section.ini",
        "tests/fixtures/meta/rank_model/rank_model_no_version_key.ini",
    ],
    ids=["no_version_section", "no_version_key"],
)
def test_parse_rank_model_file_wrong_format(file: str):
    # GIVEN a rank model file that is ill-formatted

    # WHEN parsing the rank model file
    with pytest.raises(ValidationError):
        # THEN a Pydantic validation error is raised as the version is None
        parse_rank_model_file(file)
