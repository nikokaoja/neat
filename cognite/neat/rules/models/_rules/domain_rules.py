import math
from typing import Any, ClassVar

from pydantic import Field, field_serializer, field_validator, model_serializer
from pydantic_core.core_schema import SerializationInfo

from ._types import ParentClassType, PropertyType, SemanticValueType, StrOrListType
from .base import (
    BaseMetadata,
    RoleTypes,
    RuleModel,
    SheetEntity,
    SheetList,
)


class DomainMetadata(BaseMetadata):
    role: ClassVar[RoleTypes] = RoleTypes.domain_expert
    creator: StrOrListType


class DomainProperty(SheetEntity):
    property_: PropertyType = Field(alias="Property")
    value_type: SemanticValueType = Field(alias="Value Type")
    min_count: int | None = Field(alias="Min Count", default=None)
    max_count: int | float | None = Field(alias="Max Count", default=None)

    @field_serializer("max_count", when_used="json-unless-none")
    def serialize_max_count(self, value: int | float | None) -> int | float | None | str:
        if isinstance(value, float) and math.isinf(value):
            return None
        return value

    @field_validator("max_count", mode="before")
    def parse_max_count(cls, value: int | float | None) -> int | float | None:
        if value is None:
            return float("inf")
        return value


class DomainClass(SheetEntity):
    description: str | None = Field(None, alias="Description")
    parent: ParentClassType = Field(alias="Parent Class")


class DomainRules(RuleModel):
    metadata: DomainMetadata = Field(alias="Metadata")
    properties: SheetList[DomainProperty] = Field(alias="Properties")
    classes: SheetList[DomainClass] | None = Field(None, alias="Classes")
    reference: "DomainRules | None" = Field(None, alias="Reference")
    is_reference: bool = False

    @model_serializer(mode="plain", when_used="always")
    def domain_rules_serializer(self, info: SerializationInfo) -> dict[str, Any]:
        kwargs = vars(info)
        output: dict[str, Any] = {
            "Metadata" if info.by_alias else "metadata": self.metadata.model_dump(**kwargs),
            "Properties" if info.by_alias else "properties": [prop.model_dump(**kwargs) for prop in self.properties],
        }
        if self.classes or not info.exclude_none:
            output["Classes" if info.by_alias else "classes"] = [
                cls.model_dump(**kwargs) for cls in self.classes or []
            ] or None
        return output

    def reference_self(self) -> "DomainRules":
        """DomainRules does not have reference field, so it returns a copy of itself."""
        return self.copy(deep=True)
