import json
import re
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from cognite.client import CogniteClient
from cognite.client.data_classes import Asset, AssetFilter, AssetList
from rdflib import RDF, Literal, Namespace

from cognite.neat.constants import DEFAULT_NAMESPACE
from cognite.neat.graph.extractors._base import BaseExtractor
from cognite.neat.graph.models import Triple
from cognite.neat.utils.utils import create_sha256_hash, string_to_ideal_type


class AssetsExtractor(BaseExtractor):
    """Extract data from Cognite Data Fusions Assets into Neat.

    Args:
        assets (Iterable[Asset]): An iterable of assets.
        namespace (Namespace, optional): The namespace to use. Defaults to DEFAULT_NAMESPACE.
        to_type (Callable[[Asset], str | None], optional): A function to convert an asset to a type. Defaults to None.
            If None or if the function returns None, the asset will be set to the default type "Asset".
        total (int, optional): The total number of assets to load. If passed, you will get a progress bar if rich
            is installed. Defaults to None.
        limit (int, optional): The maximal number of assets to load. Defaults to None. This is typically used for
            testing setup of the extractor. For example, if you are extracting 100 000 assets, you might want to
            limit the extraction to 1000 assets to test the setup.
        unpack_metadata (bool, optional): Whether to unpack metadata. Defaults to False, which yields the metadata as
            a JSON string.
    """

    _SPACE_PATTERN = re.compile(r"\s+")

    def __init__(
        self,
        assets: Iterable[Asset],
        namespace: Namespace | None = None,
        to_type: Callable[[Asset], str | None] | None = None,
        total: int | None = None,
        limit: int | None = None,
        unpack_metadata: bool = True,
    ):
        self.namespace = namespace or DEFAULT_NAMESPACE
        self.assets = assets
        self.to_type = to_type
        self.total = total
        self.limit = min(limit, total) if limit and total else limit
        self.unpack_metadata = unpack_metadata

    @classmethod
    def from_dataset(
        cls,
        client: CogniteClient,
        data_set_external_id: str,
        namespace: Namespace | None = None,
        to_type: Callable[[Asset], str | None] | None = None,
        limit: int | None = None,
        unpack_metadata: bool = True,
    ):
        total = client.assets.aggregate_count(filter=AssetFilter(data_set_ids=[{"externalId": data_set_external_id}]))

        return cls(
            cast(
                Iterable[Asset],
                client.assets(data_set_external_ids=data_set_external_id),
            ),
            namespace,
            to_type,
            total,
            limit,
            unpack_metadata=unpack_metadata,
        )

    @classmethod
    def from_hierarchy(
        cls,
        client: CogniteClient,
        root_asset_external_id: str,
        namespace: Namespace | None = None,
        to_type: Callable[[Asset], str | None] | None = None,
        limit: int | None = None,
        unpack_metadata: bool = True,
    ):
        total = client.assets.aggregate_count(
            filter=AssetFilter(asset_subtree_ids=[{"externalId": root_asset_external_id}])
        )

        return cls(
            cast(
                Iterable[Asset],
                client.assets(asset_subtree_external_ids=root_asset_external_id),
            ),
            namespace,
            to_type,
            total,
            limit,
            unpack_metadata=unpack_metadata,
        )

    @classmethod
    def from_file(
        cls,
        file_path: str,
        namespace: Namespace | None = None,
        to_type: Callable[[Asset], str] | None = None,
        limit: int | None = None,
        unpack_metadata: bool = True,
    ):
        return cls(
            AssetList.load(Path(file_path).read_text()),
            namespace,
            to_type,
            limit,
            unpack_metadata=unpack_metadata,
        )

    def extract(self) -> Iterable[Triple]:
        """Extracts an asset with the given asset_id."""
        if self.total:
            try:
                from rich.progress import track
            except ModuleNotFoundError:
                to_iterate = self.assets
            else:
                to_iterate = track(
                    self.assets,
                    total=self.limit or self.total,
                    description="Extracting Assets",
                )
        else:
            to_iterate = self.assets
        for no, asset in enumerate(to_iterate):
            yield from self._asset2triples(asset)
            if self.limit and no >= self.limit:
                break

    def _asset2triples(self, asset: Asset) -> list[Triple]:
        """Converts an asset to triples."""
        id_ = self.namespace[f"Asset_{asset.id}"]

        # Set rdf type
        type_ = "Asset"
        if self.to_type:
            type_ = self.to_type(asset) or type_
        type_ = self._SPACE_PATTERN.sub("_", type_)

        triples: list[Triple] = [(id_, RDF.type, self.namespace[type_])]

        # Create attributes
        if asset.name:
            triples.append((id_, self.namespace.name, Literal(asset.name)))

        if asset.description:
            triples.append((id_, self.namespace.description, Literal(asset.description)))

        if asset.external_id:
            triples.append((id_, self.namespace.external_id, Literal(asset.external_id)))

        if asset.source:
            triples.append((id_, self.namespace.source, Literal(asset.source)))

        # properties ref creation and update
        triples.append(
            (
                id_,
                self.namespace.created_time,
                Literal(datetime.fromtimestamp(asset.created_time / 1000, timezone.utc)),
            )
        )
        triples.append(
            (
                id_,
                self.namespace.last_updated_time,
                Literal(datetime.fromtimestamp(asset.last_updated_time / 1000, timezone.utc)),
            )
        )

        if asset.labels:
            for label in asset.labels:
                # external_id can create ill-formed URIs, so we create websafe URIs
                # since labels do not have internal ids, we use the external_id as the id
                triples.append(
                    (
                        id_,
                        self.namespace.label,
                        self.namespace[f"Label_{create_sha256_hash(label.dump()['externalId'])}"],
                    )
                )

        if asset.metadata:
            if self.unpack_metadata:
                for key, value in asset.metadata.items():
                    if value:
                        triples.append(
                            (
                                id_,
                                self.namespace[key],
                                Literal(string_to_ideal_type(value)),
                            )
                        )
            else:
                triples.append((id_, self.namespace.metadata, Literal(json.dumps(asset.metadata))))

        # Create connections:
        if asset.parent_id:
            triples.append((id_, self.namespace.parent, self.namespace[f"Asset_{asset.parent_id}"]))

        if asset.root_id:
            triples.append((id_, self.namespace.root, self.namespace[f"Asset_{asset.root_id}"]))

        if asset.data_set_id:
            triples.append(
                (
                    id_,
                    self.namespace.dataset,
                    self.namespace[f"Dataset_{asset.data_set_id}"],
                )
            )

        return triples
