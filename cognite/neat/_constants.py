from pathlib import Path

from cognite.client.data_classes.data_modeling.ids import DataModelId
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, XSD, Namespace, URIRef

from cognite import neat

PACKAGE_DIRECTORY = Path(neat.__file__).parent
COGNITE_MODELS = (
    DataModelId("cdf_cdm", "CogniteCore", "v1"),
    DataModelId("cdf_idm", "CogniteProcessIndustries", "v1"),
)
DMS_LISTABLE_PROPERTY_LIMIT = 1000

EXAMPLE_RULES = PACKAGE_DIRECTORY / "_rules" / "examples"
EXAMPLE_GRAPHS = PACKAGE_DIRECTORY / "_graph" / "examples"
EXAMPLE_WORKFLOWS = PACKAGE_DIRECTORY / "_workflows" / "examples"

DEFAULT_SPACE_URI = "http://purl.org/cognite/{space}#"
DEFAULT_NAMESPACE = Namespace("http://purl.org/cognite/neat#")
DEFAULT_BASE_URI = URIRef(DEFAULT_NAMESPACE)
CLASSIC_CDF_NAMESPACE = Namespace("http://purl.org/cognite/cdf-classic#")
UNKNOWN_TYPE = DEFAULT_NAMESPACE.UnknownType


def get_default_prefixes() -> dict[str, Namespace]:
    return {
        "rdf": RDF._NS,
        "rdfs": RDFS._NS,
        "dct": DCTERMS._NS,
        "skos": SKOS._NS,
        "owl": OWL._NS,
        "xsd": XSD._NS,
        "pav": Namespace("http://purl.org/pav/"),
    }


DEFAULT_URI = ""

DEFAULT_DOCS_URL = "https://cognite-neat.readthedocs-hosted.com/en/latest/"

DMS_CONTAINER_PROPERTY_SIZE_LIMIT = 100
DMS_VIEW_CONTAINER_SIZE_LIMIT = 10
