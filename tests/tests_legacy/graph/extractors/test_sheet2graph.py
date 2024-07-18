from rdflib import XSD, Literal

from cognite.neat.legacy.graph import extractors
from cognite.neat.legacy.graph.stores import MemoryStore
from cognite.neat.utils.rdf_ import remove_namespace_from_uri
from tests import config


def test_sheet2graph(simple_rules):
    graph_store = MemoryStore(prefixes=simple_rules.prefixes, namespace=simple_rules.metadata.namespace)
    graph_store.init_graph(base_prefix=simple_rules.metadata.prefix)

    triples = extractors.GraphCapturingSheet(simple_rules, config.GRAPH_CAPTURING_SHEET, use_source_ids=True).extract()

    graph_store.add_triples(triples)

    count_dict = {
        remove_namespace_from_uri(res[0]): int(res[1])
        for res in list(
            graph_store.graph.query(
                "SELECT ?class (count(?s) as ?instances ) WHERE { ?s a ?class . } "
                "group by ?class order by DESC(?instances)"
            )
        )
    }

    assert next(iter(graph_store.graph.query("Select ?o WHERE { neat:Country-1 neat:TSO ?o }")))[0] == Literal(
        "Statnett", datatype=XSD.string
    )
    assert count_dict == {"PriceArea": 2, "CountryGroup": 1, "Country": 1, "PriceAreaConnection": 1}
