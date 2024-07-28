from cg.models.lims.sample import LimsProject, LimsSample, Udf


def test_instantiate_lims_sample_model(lims_sample_raw: dict[str, str]):
    """Tests LIMS sample dict against a LIMS sample pydantic model."""

    # GIVEN a LIMS sample

    # WHEN instantiating
    lims_sample = LimsSample.model_validate(lims_sample_raw)

    # THEN assert that it was successfully created
    assert isinstance(lims_sample, LimsSample)


def test_instantiate_lims_udf_model(lims_udfs_raw: dict[str, str]):
    """Tests LIMS UDFs dict against a LIMS UDF pydantic model."""

    # GIVEN LIMS UDFs

    # WHEN instantiating
    lims_udf = Udf.model_validate(lims_udfs_raw)

    # THEN assert that it was successfully created
    assert isinstance(lims_udf, Udf)

    # THEN the sex should be set
    assert lims_udf.sex == "M"


def test_instantiate_lims_project_model(lims_project_raw: dict[str, str]):
    """Tests LIMS projwct dict against a LIMS project pydantic model."""

    # GIVEN LIMS project

    # WHEN instantiating
    lims_project = LimsProject.model_validate(lims_project_raw)

    # THEN assert that it was successfully created
    assert isinstance(lims_project, LimsProject)
