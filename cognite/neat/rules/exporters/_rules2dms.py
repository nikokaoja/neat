import warnings
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from cognite.client import CogniteClient
from cognite.client.data_classes._base import CogniteResourceList
from cognite.client.exceptions import CogniteAPIError

from cognite.neat.rules.models._rules.dms_architect_rules import DMSRules
from cognite.neat.rules.models._rules.dms_schema import DMSSchema
from cognite.neat.utils.cdf_loaders import ContainerLoader, DataModelingLoader, DataModelLoader, SpaceLoader, ViewLoader

from ._base import CDFExporter
from ._models import UploadResult


class DMSExporter(CDFExporter[DMSSchema]):
    """Class for exporting rules object to CDF Data Model Storage (DMS).

    Args:
        rules: Domain Model Service Architect rules object.
    """

    def __init__(
        self,
        rules: DMSRules,
        export_components: frozenset[Literal["all", "spaces", "data_models", "views", "containers"]] = frozenset(
            {"all"}
        ),
        include_space: set[str] | None = None,
        existing_handling: Literal["fail", "skip", "update", "force"] = "update",
    ):
        self.rules = rules
        self.export_components = export_components
        self.include_space = include_space
        self.existing_handling = existing_handling
        self._schema: DMSSchema | None = None

    def export_to_file(self, filepath: Path) -> None:
        if filepath.suffix not in {".zip"}:
            warnings.warn("File extension is not .zip, adding it to the file name", stacklevel=2)
            filepath = filepath.with_suffix(".zip")

        schema = self.export()
        with zipfile.ZipFile(filepath, "w") as zip_ref:
            for space in schema.spaces:
                zip_ref.writestr(f"data_models/{space.space}.space.yaml", space.dump_yaml())
            for model in schema.data_models:
                zip_ref.writestr(f"data_models/{model.external_id}.datamodel.yaml", model.dump_yaml())
            for view in schema.views:
                zip_ref.writestr(f"data_models/{view.external_id}.view.yaml", view.dump_yaml())
            for container in schema.containers:
                zip_ref.writestr(f"data_models/{container.external_id}.container.yaml", container.dump_yaml())

    def export(self) -> DMSSchema:
        if self._schema is None:
            self._schema = self.rules.as_schema()
        return self._schema

    def export_to_cdf(self, client: CogniteClient, dry_run: bool = False) -> Iterable[UploadResult]:
        schema = self.export()
        to_export: list[tuple[CogniteResourceList, DataModelingLoader]] = []
        if self.export_components.intersection({"all", "spaces"}):
            to_export.append((schema.spaces, SpaceLoader(client)))
        if self.export_components.intersection({"all", "containers"}):
            to_export.append((schema.containers, ContainerLoader(client)))
        if self.export_components.intersection({"all", "views"}):
            to_export.append((schema.views, ViewLoader(client, self.existing_handling)))
        if self.export_components.intersection({"all", "data_models"}):
            to_export.append((schema.data_models, DataModelLoader(client)))

        for items, loader in to_export:
            item_ids = loader.get_ids(items)
            cdf_items = loader.retrieve(item_ids)
            cdf_item_by_id = {loader.get_id(item): item for item in cdf_items}
            to_create, to_update, unchanged = [], [], []
            for item in items:
                if self.include_space is not None and not loader.in_space(item, self.include_space):
                    continue
                cdf_item = cdf_item_by_id.get(loader.get_id(item))
                if cdf_item is None:
                    to_create.append(item)
                elif loader.are_equal(item, cdf_item):
                    unchanged.append(item)
                else:
                    to_update.append(item)
            created = len(to_create)
            failed_created = 0

            skipped = 0
            if self.existing_handling in ["update", "force"]:
                changed = len(to_update)
                failed_changed = 0
            elif self.existing_handling == "skip":
                changed = 0
                failed_changed = 0
                skipped += len(to_update)
            elif self.existing_handling == "fail":
                failed_changed = len(to_update)
                changed = 0
            else:
                raise ValueError(f"Unsupported existing_handling {self.existing_handling}")

            error_messages: list[str] = []
            if not dry_run:
                to_create = loader.sort_by_dependencies(to_create)
                try:
                    loader.create(to_create)
                except CogniteAPIError as e:
                    failed_created = len(e.failed) + len(e.unknown)
                    created -= failed_created
                    error_messages.append(e.message)

                if self.existing_handling in ["update", "force"]:
                    try:
                        loader.update(to_update)
                    except CogniteAPIError as e:
                        failed_changed = len(e.failed) + len(e.unknown)
                        changed -= failed_changed
                        error_messages.append(e.message)

            yield UploadResult(
                name=loader.resource_name,
                created=len(to_create),
                changed=len(to_update),
                unchanged=len(unchanged),
                skipped=skipped,
                failed_created=failed_created,
                failed_changed=failed_changed,
                error_messages=error_messages,
            )
