from pathlib import Path
from typing import cast

import pytest
from cognite.client import data_modeling as dm

from cognite.neat.rules.importers import DMSImporter, ExcelImporter
from cognite.neat.rules.issues.dms import DirectRelationMissingSourceWarning
from cognite.neat.rules.models import DMSRules, DMSSchema, RoleTypes
from tests.config import DOC_RULES


class TestDMSImporter:
    def test_import_with_direct_relation_none(self) -> None:
        importer = DMSImporter(SCHEMA_WITH_DIRECT_RELATION_NONE)

        rules, issues = importer.to_rules(errors="continue")

        assert len(issues) == 1
        assert issues[0] == DirectRelationMissingSourceWarning(dm.ViewId("neat", "OneView", "1"), "direct")
        dms_rules = cast(DMSRules, rules)
        dump_dms = dms_rules.model_dump()
        assert dump_dms["properties"][0]["value_type"] == "#N/A"
        assert dump_dms["properties"][0]["name"] == "direct"
        assert dump_dms["properties"][0]["description"] == "Direction Relation"
        assert dump_dms["views"][0]["name"] == "OneView"
        assert dump_dms["views"][0]["description"] == "One View"

        info_rules = dms_rules.as_information_architect_rules()
        dump_info = info_rules.model_dump()
        assert dump_info["properties"][0]["value_type"] == "#N/A"

    @pytest.mark.parametrize(
        "filepath",
        [
            pytest.param(DOC_RULES / "cdf-dms-architect-alice.xlsx", id="Alice rules"),
            pytest.param(DOC_RULES / "dms-analytics-olav.xlsx", id="Olav DMS rules"),
        ],
    )
    def test_import_rules_from_tutorials(self, filepath: Path) -> None:
        dms_rules = cast(DMSRules, ExcelImporter(filepath).to_rules(errors="raise", role=RoleTypes.dms_architect))
        # We must have the reference to be able to convert back to schema
        schema = dms_rules.as_schema()
        dms_importer = DMSImporter(schema)

        rules, issues = dms_importer.to_rules(errors="continue")
        issue_str = "\n".join([issue.message() for issue in issues])
        assert rules is not None, f"Failed to import rules {issue_str}"
        assert isinstance(rules, DMSRules)
        # This information is lost in the conversion to schema
        exclude = {
            "metadata": {"created", "updated"},
            "properties": {"__all__": {"reference"}},
            "reference": {},
            "views": {"__all__": {"reference"}},
        }
        assert rules.model_dump(exclude=exclude) == dms_rules.model_dump(exclude=exclude)


SCHEMA_WITH_DIRECT_RELATION_NONE = DMSSchema(
    data_model=dm.DataModelApply(
        space="neat",
        external_id="data_model",
        version="1",
        views=[
            dm.ViewId("neat", "OneView", "1"),
        ],
    )
)
SCHEMA_WITH_DIRECT_RELATION_NONE.spaces.append(dm.SpaceApply(space="neat"))
SCHEMA_WITH_DIRECT_RELATION_NONE.containers.append(
    dm.ContainerApply(
        space="neat",
        external_id="container",
        properties={"direct": dm.ContainerProperty(type=dm.DirectRelation())},
    )
)
SCHEMA_WITH_DIRECT_RELATION_NONE.views.append(
    dm.ViewApply(
        space="neat",
        external_id="OneView",
        version="1",
        name="OneView",
        description="One View",
        properties={
            "direct": dm.MappedPropertyApply(
                container=dm.ContainerId("neat", "container"),
                container_property_identifier="direct",
                source=None,
                name="direct",
                description="Direction Relation",
            )
        },
    )
)
