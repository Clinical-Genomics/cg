"""Test CG CLI upload observations module."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.upload.observations import upload_observations_to_loqusdb
from cg.cli.upload.observations.utils import (
    get_observations_api,
    get_observations_verified_case,
)
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import Workflow
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.exc import CaseNotFoundError
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_observations(
    cg_context: CGConfig, cli_runner: CliRunner, helpers: StoreHelpers, caplog: LogCaptureFixture
):
    """Test upload of observations."""
    caplog.set_level(logging.DEBUG)
    store: Store = cg_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    link: CaseSample = store.relate_sample(case=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    store.session.add(link)

    # WHEN trying to do a dry run upload to Loqusdb
    result = cli_runner.invoke(
        upload_observations_to_loqusdb, [case.internal_id, "--dry-run"], obj=cg_context
    )

    # THEN the execution should have been successful and stop at a dry run step
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry run" in caplog.text


def test_get_observations_case(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get observations supported case."""
    store: Store = cg_context.status_db

    # GIVEN an observations valid case
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True

    # WHEN retrieving a case given a specific case ID
    extracted_case: Case = get_observations_verified_case(cg_context, case.internal_id, upload=True)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_case_invalid_id(cg_context: CGConfig, caplog: LogCaptureFixture):
    """Test get observations case providing an incorrect ID."""
    caplog.set_level(logging.DEBUG)

    # WHEN retrieving a case given a specific case ID
    with pytest.raises(CaseNotFoundError):
        # THEN a CaseNotFoundError should be raised
        get_observations_verified_case(cg_context, "invalid_case_id", upload=True)

    assert "Invalid case ID. Retrieving available cases for Loqusdb actions." in caplog.text


def test_get_observations_case_to_upload(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get case ready to be uploaded to Loqusdb."""
    store: Store = cg_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True

    # WHEN retrieving a case given a specific case ID
    extracted_case: Case = get_observations_verified_case(cg_context, case.internal_id, upload=True)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_api(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get observation API given a Loqusdb supported case."""
    store: Store = cg_context.status_db

    # GIVEN a Loqusdb supported case
    case: Case = helpers.add_case(store, data_analysis=Workflow.MIP_DNA)
    sample: Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    link: CaseSample = store.relate_sample(case=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    store.session.add(link)

    # WHEN retrieving the observation API
    observations_api: MipDNAObservationsAPI = get_observations_api(
        context=cg_context, case_id=case.internal_id, upload=True
    )

    # THEN a MIP-DNA API should be returned
    assert observations_api
    assert isinstance(observations_api, MipDNAObservationsAPI)
