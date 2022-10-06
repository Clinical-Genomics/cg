"""Test CG CLI upload observations module."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.loqus import LoqusdbAPI
from cg.cli.upload.observations import observations
from cg.cli.upload.observations.utils import (
    get_observations_case,
    get_observations_case_to_upload,
    get_observations_api,
    get_observations_case_to_delete,
)
from cg.constants import EXIT_SUCCESS
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.exc import CaseNotFoundError
from cg.meta.upload.observations.observations_api import UploadObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.store_helpers import StoreHelpers

from tests.apps.loqus.conftest import (
    fixture_loqusdbapi,
    fixture_loqus_config,
    loqus_process,
    loqus_binary_path,
    loqus_config_path,
    fixture_loqusdb_case_output,
)


def test_observations(
    base_context: CGConfig, cli_runner: CliRunner, helpers: StoreHelpers, caplog: LogCaptureFixture
):
    """Test upload of observations."""

    caplog.set_level(logging.DEBUG)
    store: Store = base_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: models.Family = helpers.add_case(store)
    case.customer.loqus_upload = True
    sample: models.Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    store.relate_sample(family=case, sample=sample, status=PhenotypeStatus.UNKNOWN)

    # WHEN trying to do a dry run upload to Loqusdb
    result = cli_runner.invoke(observations, [case.internal_id, "--dry-run"], obj=base_context)

    # THEN the execution should have been successful and stop at a dry run step
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry run" in caplog.text


def test_get_observations_case(base_context: CGConfig, helpers: StoreHelpers):
    """Test get observations supported case."""

    store: Store = base_context.status_db

    # GIVEN an observations valid case
    case: models.Family = helpers.add_case(store)

    # WHEN retrieving a case given a specific case ID
    extracted_case = get_observations_case(base_context, case.internal_id, upload=True)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_case_invalid_id(base_context: CGConfig, caplog: LogCaptureFixture):
    """Test get observations case providing an incorrect ID."""

    caplog.set_level(logging.DEBUG)

    # WHEN retrieving a case given a specific case ID
    with pytest.raises(CaseNotFoundError):
        # THEN a CaseNotFoundError should be raised
        get_observations_case(base_context, "invalid_case_id", upload=True)

    assert "Invalid case ID. Retrieving available cases for Loqusdb actions." in caplog.text


def test_get_observations_case_to_upload(base_context: CGConfig, helpers: StoreHelpers):
    """Test get case ready to be uploaded to Loqusdb."""

    store: Store = base_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: models.Family = helpers.add_case(store)
    case.customer.loqus_upload = True

    # WHEN retrieving a case given a specific case ID
    extracted_case = get_observations_case_to_upload(base_context, case.internal_id)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_case_to_delete(
    base_context: CGConfig,
    helpers: StoreHelpers,
    loqusdbapi: LoqusdbAPI,
    loqusdb_case_output: bytes,
):
    """Test get case ready to be deleted from Loqusdb."""

    store: Store = base_context.status_db

    # GIVEN an observations instance and a case ready to be deleted from Loqusdb
    loqusdbapi.process.stdout = loqusdb_case_output.decode("utf-8").rstrip()
    base_context.loqusdb_api_ = loqusdbapi
    case: models.Family = helpers.add_case(store)

    # WHEN retrieving a case to delete given a specific case ID
    extracted_case = get_observations_case_to_delete(base_context, case.internal_id)

    # THEN the extracted case should match the stored one
    assert case == extracted_case


def test_get_observations_api(base_context: CGConfig, helpers: StoreHelpers):
    """Test get observation API given a Loqusdb supported case."""

    store: Store = base_context.status_db

    # GIVEN a Loqusdb supported case
    case: models.Family = helpers.add_case(store)
    sample: models.Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    store.relate_sample(family=case, sample=sample, status=PhenotypeStatus.UNKNOWN)

    # WHEN retrieving the observation API
    observations_api: UploadObservationsAPI = get_observations_api(base_context, case)

    # THEN the API should be returned
    assert observations_api
