from pathlib import Path
from unittest import mock

import pytest

from cg.constants.constants import FileFormat
from cg.exc import CgDataError
from cg.io.controller import WriteFile
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.store.models import Case, Organism, Sample
from cg.store.store import Store


@pytest.fixture
def microsalt_case(microsalt_config_file_creator: MicrosaltConfigFileCreator) -> Case:
    return microsalt_config_file_creator.store.get_cases()[0]


@pytest.fixture
def microsalt_sample(microsalt_case: Case) -> Sample:
    return microsalt_case.samples[0]


def test_create_success(
    microsalt_config_file_creator: MicrosaltConfigFileCreator, microsalt_case: Case
):
    # GIVEN a microsalt_config_file_creator
    with mock.patch.object(WriteFile, "write_file_from_content", return_value=True) as file_writer:
        # WHEN creating a microsalt config file
        microsalt_config_file_creator.create(microsalt_case.internal_id)
        # THEN it should be written to disk as json
        file_writer.assert_called_once_with(
            content=mock.ANY,
            file_format=FileFormat.JSON,
            file_path=Path(
                microsalt_config_file_creator.queries_path,
                f"{microsalt_case.internal_id}.{FileFormat.JSON}",
            ),
        )


def test_create_failure_missing_organism(
    microsalt_config_file_creator: MicrosaltConfigFileCreator,
    microsalt_case: Case,
    microsalt_sample: Sample,
):
    # GIVEN a microSALT case containing a sample with a missing organism
    microsalt_sample.organism = None

    with pytest.raises(CgDataError) as error:
        # WHEN creating the case's config file
        # THEN the method should raise a CgDataError
        microsalt_config_file_creator.create(microsalt_case.internal_id)
    assert str(error.value) == "Organism missing on Sample"


def test_organism_override(microsalt_store: Store, microsalt_sample: Sample):

    # GIVEN a store containing specific organisms
    organism_1: Organism = microsalt_store.add_organism(
        internal_id="gonorrhoeae borealis", name="Aurora"
    )
    organism_2: Organism = microsalt_store.add_organism(
        internal_id="Cutibacterium acnes borealis", name="Aurora"
    )

    # GIVEN that a sample specifies organism_1
    microsalt_sample.organism = organism_1

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(microsalt_sample) == "Neisseria spp."

    # GIVEN that a sample specifies organism_2
    microsalt_sample.organism = organism_2

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(microsalt_sample) == "Propionibacterium acnes"


def test_reference_genome_override(
    microsalt_store: Store, microsalt_case: Case, microsalt_sample: Sample
):

    # GIVEN a store containing VRE organisms
    organism_1: Organism = microsalt_store.add_organism(
        internal_id="VRE", name="VRE", reference_genome="NC_017960.1"
    )
    organism_2: Organism = microsalt_store.add_organism(
        internal_id="VRE", name="VRE", reference_genome="NC_004668.1"
    )

    # GIVEN that a sample specifies organism_1
    microsalt_sample.organism = organism_1

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(microsalt_sample) == "Enterococcus faecium"

    # GIVEN that a sample specifies organism_2
    microsalt_sample.organism = organism_2

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(microsalt_sample) == "Enterococcus faecalis"
