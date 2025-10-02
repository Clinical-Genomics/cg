def test_create_wgs_tumor_only():
    # GIVEN a case with one tumor WGS sample
    wgs_tumor_only_case: Mock[Case] = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1"
    )
    application: Mock[Application] = create_autospec(Application, prep_category="wgs")
    application_version: Mock[ApplicationVersion] = create_autospec(
        ApplicationVersion, application=application
    )
    sample_1: Mock[Sample] = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        application_version=application_version,
    )
    wgs_tumor_only_case.samples = [sample_1]
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # WHEN building the CLI input
    cli_input: BalsamicConfigInput = balsamic_configurator._build_cli_input(
        case_id=wgs_tumor_only_case.internal_id
    )

    # THEN pydantic model should be created (and validated)
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name is None

    # THEN the correct gens_coverage_pon should be chosen (Female)
    assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_female_path

    # THEN fields not relevant for WGS analyses should be set to their default values
    for field in PANEL_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default
