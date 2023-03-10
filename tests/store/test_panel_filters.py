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


def test_filter_panel_by_abbrev_returns_none_when_abbrev_does_not_exist(store_with_panels: Store):
    """Test finding a panel by abbreviation when the abbreviation does not exist in the store."""

    # GIVEN a store with panels
    panel_query = store_with_panels._get_panel_query()
    assert panel_query.count() > 0

    # WHEN finding a panel by an abbreviation that does not exist
    filtered_panels = filter_panel_by_abbrev(panel_query, "nonexistent_abbrev").all()

    # THEN no panels should be returned
    assert len(filtered_panels) == 0
