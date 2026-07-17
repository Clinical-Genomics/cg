from pathlib import Path
from unittest.mock import Mock, call

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators import rank_model_file_copier
from cg.services.analysis_starter.configurator.file_creators.rank_model_file_copier import (
    RankModelFileCopier,
)


def test_copy(mocker: MockerFixture):
    # GIVEN a RankModelFileCopier
    RankModelFileCopier()

    # GIVEN two paths
    rank_model_snv = Path("/one/glorious/path.ini")
    rank_model_sv = Path("/second/glorious/path.ini")

    # GIVEN a directory
    directory = Path("/a/victorious/directory/")

    # GIVEN a mocked io copy function
    mocked_copy_file: Mock = mocker.patch.object(rank_model_file_copier, "copy_file")

    # WHEN calling copy
    RankModelFileCopier.copy(
        source_snv_file=rank_model_snv, source_sv_file=rank_model_sv, target_directory=directory
    )

    # THEN the correct calls have been made
    mocked_copy_file.assert_has_calls(
        [
            call(from_path=rank_model_snv, to_path=directory),
            call(from_path=rank_model_sv, to_path=directory),
        ]
    )
