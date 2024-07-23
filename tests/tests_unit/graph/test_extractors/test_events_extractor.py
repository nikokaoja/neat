from cognite.client.data_classes import EventList
from cognite.client.testing import monkeypatch_cognite_client
from rdflib import Graph

from cognite.neat.graph.extractors import EventsExtractor
from tests.config import CLASSIC_CDF_EXTRACTOR_DATA


def test_events_extractor():
    with monkeypatch_cognite_client() as client_mock:
        events = EventList.load((CLASSIC_CDF_EXTRACTOR_DATA / "events.yaml").read_text())
        client_mock.events.return_value = events
        client_mock.events.aggregate_count.return_value = len(events)

    g = Graph()

    for triple in EventsExtractor.from_dataset(client_mock, data_set_external_id="some_event_dataset").extract():
        g.add(triple)

    assert len(g) == 18
