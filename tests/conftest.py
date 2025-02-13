from typing import Any

import pandas as pd
import pytest

from cognite.neat._rules.importers import ExcelImporter
from cognite.neat._rules.models import (
    AssetRules,
    DMSRules,
    DomainRules,
    InformationRules,
    RoleTypes,
)
from cognite.neat._rules.models.dms import DMSInputRules
from cognite.neat._rules.transformers import ImporterPipeline
from cognite.neat._utils.spreadsheet import read_individual_sheet
from tests.config import DATA_FOLDER, DOC_RULES


@pytest.fixture(scope="session")
def alice_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "cdf-dms-architect-alice.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", False, ["View Property"]),
        "Views": read_individual_sheet(excel_file, "Views", False, ["View"]),
        "Containers": read_individual_sheet(excel_file, "Containers", False, ["Container"]),
    }


@pytest.fixture(scope="session")
def alice_rules(alice_spreadsheet: dict[str, dict[str, Any]]) -> DMSRules:
    return DMSInputRules.load(alice_spreadsheet).as_rules()


@pytest.fixture(scope="session")
def david_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "information-architect-david.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def david_rules(david_spreadsheet: dict[str, dict[str, Any]]) -> InformationRules:
    return InformationRules.model_validate(david_spreadsheet)


@pytest.fixture(scope="session")
def asset_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DATA_FOLDER / "asset-architect-test.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def asset_rules(asset_spreadsheet: dict[str, dict[str, Any]]) -> AssetRules:
    return AssetRules.model_validate(asset_spreadsheet)


@pytest.fixture(scope="session")
def jimbo_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "asset-architect-jimbo.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
        "Prefixes": read_individual_sheet(excel_file, "Prefixes", expected_headers=["Prefix"]),
    }


@pytest.fixture(scope="session")
def jimbo_rules(jimbo_spreadsheet: dict[str, dict[str, Any]]) -> AssetRules:
    return AssetRules.model_validate(jimbo_spreadsheet)


@pytest.fixture(scope="session")
def jon_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "expert-wind-energy-jon.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
    }


@pytest.fixture(scope="session")
def jon_rules(jon_spreadsheet: dict[str, dict[str, Any]]) -> DomainRules:
    return DomainRules.model_validate(jon_spreadsheet)


@pytest.fixture(scope="session")
def emma_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "expert-grid-emma.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def emma_rules(emma_spreadsheet: dict[str, dict[str, Any]]) -> DomainRules:
    return DomainRules.model_validate(emma_spreadsheet)


@pytest.fixture(scope="session")
def olav_rules() -> InformationRules:
    return ImporterPipeline.verify(
        ExcelImporter(DOC_RULES / "information-analytics-olav.xlsx"), role=RoleTypes.information
    )


@pytest.fixture(scope="session")
def olav_dms_rules() -> DMSRules:
    return ImporterPipeline.verify(ExcelImporter(DOC_RULES / "dms-analytics-olav.xlsx"), role=RoleTypes.dms)


@pytest.fixture(scope="session")
def svein_harald_information_rules() -> InformationRules:
    return ImporterPipeline.verify(
        ExcelImporter(DOC_RULES / "information-addition-svein-harald.xlsx"), role=RoleTypes.information
    )


@pytest.fixture(scope="session")
def svein_harald_dms_rules() -> DMSRules:
    return ImporterPipeline.verify(ExcelImporter(DOC_RULES / "dms-addition-svein-harald.xlsx"), role=RoleTypes.dms)


@pytest.fixture(scope="session")
def olav_rebuild_dms_rules() -> DMSRules:
    return ImporterPipeline.verify(ExcelImporter(DOC_RULES / "dms-rebuild-olav.xlsx"), role=RoleTypes.dms)


@pytest.fixture(scope="session")
def camilla_information_rules() -> InformationRules:
    return ImporterPipeline.verify(
        ExcelImporter(DOC_RULES / "information-business-camilla.xlsx"), role=RoleTypes.information
    )
