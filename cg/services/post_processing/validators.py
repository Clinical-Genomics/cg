from cg.services.post_processing.exc import PostProcessingRunValidationError


def validate_name_pre_fix(run_name: str) -> None:
    if not run_name.startswith("r"):
        raise PostProcessingRunValidationError


def validate_has_expected_parts(run_name: str, expected_parts: int) -> None:
    if len(run_name.split("/")) != expected_parts:
        raise PostProcessingRunValidationError
