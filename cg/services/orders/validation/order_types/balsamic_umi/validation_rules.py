from cg.services.orders.validation.order_types.balsamic.validation_rules import (
    BALSAMIC_CASE_RULES,
    BALSAMIC_CASE_SAMPLE_RULES,
)

BALSAMIC_UMI_CASE_RULES: list[callable] = BALSAMIC_CASE_RULES.copy()
BALSAMIC_UMI_CASE_SAMPLE_RULES: list[callable] = BALSAMIC_CASE_SAMPLE_RULES.copy()
