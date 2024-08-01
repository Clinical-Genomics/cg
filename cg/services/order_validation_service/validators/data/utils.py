from cg.services.order_validation_service.models.errors import InvalidGenePanelsError
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.store.store import Store


def validate_panels_for_case(case: TomteCase, store: Store) -> list[InvalidGenePanelsError]:
    errors: list[InvalidGenePanelsError] = []
    invalid_panels: list[str] = get_invalid_panels(panels=case.panels, store=store)
    if invalid_panels:
        error = InvalidGenePanelsError(case_name=case.name, panels=invalid_panels)
        errors.append(error)
    return errors


def get_invalid_panels(panels: list[str], store: Store) -> list[str]:
    invalid_panels: list[str] = []
    for panel in panels:
        if not store.does_gene_panel_exist(panel):
            invalid_panels.append(panel)
    return invalid_panels


def does_list_contain_duplicates(elements: list):
    return not len(set(elements)) == len(elements)
