from cg.store.api.core import Store
from cg.store.models import Panel
from cg.store.panel_filters import filter_panel_by_abbrev


def test_filter_panel_by_abbrev_returns_correct_panel(store_with_panels: Store):
    """Test finding a panel by abbreviation when the abbreviation exists."""

    # GIVEN a store with multiple panels
    num_panels = store_with_panels._get_panel_query().count()
    assert num_panels > 0

    # Select a random panel from the store
    panel = store_with_panels._get_panel_query().first()
    assert isinstance(panel, Panel)

    # WHEN finding the panel by abbreviation
    filtered_panel = filter_panel_by_abbrev(
        panels=store_with_panels._get_panel_query(),
        abbreviation=panel.abbrev,
    ).first()

    # THEN the filtered panel should be of the correct instance and have the correct abbreviation
    assert isinstance(filtered_panel, Panel)
    assert filtered_panel.abbrev == panel.abbrev
