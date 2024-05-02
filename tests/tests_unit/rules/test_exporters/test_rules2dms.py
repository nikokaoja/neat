import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import cast

import pytest
from cognite.client import data_modeling as dm

from cognite.neat.rules import importers
from cognite.neat.rules.exporters import DMSExporter
from cognite.neat.rules.models.rules._dms_architect_rules import (
    DMSRules,
)
from cognite.neat.rules.models.rules._dms_schema import PipelineSchema
from tests.data import DMS_UNKNOWN_VALUE_TYPE, INFORMATION_UNKNOWN_VALUE_TYPE


class TestDMSExporter:
    def test_export_dms_schema_has_names_description(self, alice_rules: DMSRules) -> None:
        exporter = DMSExporter()
        schema = exporter.export(alice_rules)

        assert schema.views[0].name == "Generating Unit"
        assert schema.views[0].description == "An asset that is creating power"
        assert schema.views[0].properties["activePower"].name == "active power"
        assert schema.views[0].properties["activePower"].description == "Active power of generating unit"

    def test_export_dms_schema_to_zip(self, alice_rules: DMSRules, tmp_path: Path) -> None:
        exporter = DMSExporter()
        schema = exporter.export(alice_rules)
        zipfile_path = tmp_path / "test.zip"

        exporter.export_to_file(alice_rules, zipfile_path)

        counts = Counter()
        with zipfile.ZipFile(zipfile_path, "r") as zip_ref:
            for name in zip_ref.namelist():
                matches = re.search(r"[a-zA-Z0-9_].(space|datamodel|view|container|node).yaml$", name)
                counts.update([matches.group(1)])

        assert counts["space"] == len(schema.spaces)
        assert counts["datamodel"] == len(schema.data_models)
        assert counts["view"] == len(alice_rules.views)
        assert counts["container"] == len(alice_rules.containers)
        assert counts["node"] == len(schema.node_types)

    def test_export_dms_schema_with_pipeline(self, alice_rules: DMSRules, tmp_path) -> None:
        exporter = DMSExporter(export_pipeline=True)
        schema = cast(PipelineSchema, exporter.export(alice_rules))
        exporter.export_to_file(alice_rules, tmp_path)

        counts = Counter()
        for yaml_file in (tmp_path / "data_models").rglob("*.yaml"):
            if "." in yaml_file.stem:
                resource_type = yaml_file.stem.rsplit(".")[-1]
                counts.update([resource_type])
        transformation_count = len(list((tmp_path / "transformations").rglob("*.yaml")))
        table_count = len(list((tmp_path / "raw").rglob("*.yaml")))

        assert counts["space"] == len(schema.spaces)
        assert counts["datamodel"] == len(schema.data_models)
        assert counts["view"] == len(schema.views)
        assert counts["container"] == len(schema.containers)
        assert transformation_count == len(schema.transformations)
        assert table_count == len(schema.raw_tables)


class TestImportExportDMS:
    @pytest.mark.parametrize(
        "filepath",
        [
            pytest.param(INFORMATION_UNKNOWN_VALUE_TYPE, id="Information source"),
            pytest.param(DMS_UNKNOWN_VALUE_TYPE, id="DMS source"),
        ],
    )
    def test_import_excel_export_dms(self, filepath: Path) -> None:
        rules = importers.ExcelImporter(filepath).to_rules(errors="raise")

        exported = DMSExporter().export(rules)

        assert len(exported.views) == 1
        view = exported.views[0]
        assert view.as_id() == dm.ViewId("badmodel", "GeneratingUnit", "0.1.0")
        assert "geoLocation" in view.properties
        prop = view.properties["geoLocation"]
        assert isinstance(prop, dm.MappedPropertyApply)
        # This model is missing the value type (is set #N/A in the excel file)
        assert prop.source is None
        assert prop.container == dm.ContainerId("badmodel", "GeneratingUnit")
        assert len(exported.containers) == 1
        container = exported.containers[0]
        assert container.as_id() == dm.ContainerId("badmodel", "GeneratingUnit")
        assert "geoLocation" in container.properties
        prop = container.properties["geoLocation"]
        assert isinstance(prop, dm.ContainerProperty)
        assert prop.type == dm.DirectRelation()
