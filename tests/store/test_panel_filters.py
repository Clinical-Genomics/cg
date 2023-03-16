from sqlalchemy.orm import Query

from cg.store.api.core import Store
from cg.store.models import Panel
from cg.store.filters.panel_filters import filter_panel_by_abbrev


def test_filter_panel_by_abbrev_returns_correct_panel(store_with_panels: Store):
    """Test finding a panel by abbreviation when the abbreviation exists."""

    # GIVEN a store with multiple panels
    num_panels = store_with_panels._get_query(table=Panel).count()
    assert num_panels > 0

    # Select a random panel from the store
    panel = store_with_panels._get_query(table=Panel).first()
    assert isinstance(panel, Panel)

    # WHEN finding the panel by abbreviation
    filtered_panel_query: Query = filter_panel_by_abbrev(
        panels=store_with_panels._get_query(table=Panel),
        abbreviation=panel.abbrev,
    )

    # THEN the result is a query
    assert isinstance(filtered_panel_query, Query)

    # THEN the filtered panel is a Panel
    filtered_panel: Panel = filtered_panel_query.first()
    assert isinstance(filtered_panel, Panel)

    # THEN the filtered panel has the same abbreviation as the original panel
    assert filtered_panel.abbrev == panel.abbrev


def test_filter_panel_by_abbrev_returns_none_when_abbrev_does_not_exist(store_with_panels: Store):
    """Test finding a panel by abbreviation when the abbreviation does not exist in the store."""

    # GIVEN a store with panels
    panel_query: Query = store_with_panels._get_query(table=Panel)
    assert panel_query.count() > 0

    # WHEN finding a panel by an abbreviation that does not exist
    filtered_panels_query: Query = filter_panel_by_abbrev(panel_query, "nonexistent_abbrev")

    # THEN the result is a query
    assert isinstance(filtered_panels_query, Query)

    # THEN no panels should be returned
    assert not filtered_panels_query.all()
