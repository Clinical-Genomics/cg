from datetime import datetime

from cg.models.dolores.event import Event, EventUpload


def test_instantiate_dolores_event(dolores_event_raw: dict):
    """
    Tests Dolores event model
    """
    # GIVEN a dictionary with the some event data

    # WHEN instantiating a Event object
    dolores_event = Event(**dolores_event_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_event, Event)


def test_instantiate_dolores_event_upload(dolores_event_raw: dict, datestamp_now: datetime):
    """
    Tests Dolores event_upload model
    """
    # GIVEN a dictionary with the some event_upload data
    dolores_event_raw.update(
        {
            "uploaded_at": datestamp_now,
            "uploaded_to": "scout",
            "uploaded_to_url": "mongodb://writer@cg-mongo1-prod.scilifelab.se",
        }
    )

    # WHEN instantiating a EventUpload object
    dolores_event_upload = EventUpload(**dolores_event_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_event_upload, EventUpload)
