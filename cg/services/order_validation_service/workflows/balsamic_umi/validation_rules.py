from cg.services.order_validation_service.workflows.balsamic.validation_rules import (
    CASE_RULES as BALSAMIC_CASE_RULES,
)
from cg.services.order_validation_service.workflows.balsamic.validation_rules import (
    CASE_SAMPLE_RULES as BALSAMIC_CASE_SAMPLE_RULES,
)

CASE_RULES: list[callable] = BALSAMIC_CASE_RULES.copy()
CASE_SAMPLE_RULES: list[callable] = BALSAMIC_CASE_SAMPLE_RULES.copy()
