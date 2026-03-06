"""
Core data model primitives for openstage.

Provides system-agnostic base types for legislative data: multilingual text,
multi-scheme identifiers, and a base entity class with extra="allow" for
domain-specific attributes.
"""

from __future__ import annotations

from typing import Any, Iterator

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class MultiLangText:
    """Dict-like container mapping language codes to text strings.

    Stores multilingual text as {lang_code: text}. A plain string without
    language information is stored under the key "_".
    """

    __slots__ = ("_values",)

    def __init__(self, values: dict[str, str] | None = None) -> None:
        object.__setattr__(self, "_values", dict(values) if values else {})

    def get(self, lang: str) -> str | None:
        return self._values.get(lang)

    def preferred(self, langs: tuple[str, ...] = ("en", "fr", "de")) -> str | None:
        for lang in langs:
            if lang in self._values:
                return self._values[lang]
        if "_" in self._values:
            return self._values["_"]
        return None

    @property
    def languages(self) -> list[str]:
        return list(self._values.keys())

    def items(self):
        return self._values.items()

    def __getitem__(self, lang: str) -> str:
        return self._values[lang]

    def __contains__(self, lang: str) -> bool:
        return lang in self._values

    def __len__(self) -> int:
        return len(self._values)

    def __bool__(self) -> bool:
        return bool(self._values)

    def __str__(self) -> str:
        text = self.preferred()
        if text is not None:
            return text
        if self._values:
            return next(iter(self._values.values()))
        return ""

    def __repr__(self) -> str:
        return f"MultiLangText({self._values!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MultiLangText):
            return self._values == other._values
        return NotImplemented

    @classmethod
    def from_value(
        cls, value: Any, default_lang: str = "_"
    ) -> MultiLangText | None:
        """Build from a dict[str, str], a plain str, or None.

        - dict[str, str] -> stored directly
        - str -> stored under key ``default_lang`` (default "_")
        - None -> returns None
        """
        if value is None:
            return None
        if isinstance(value, MultiLangText):
            return value
        if isinstance(value, dict):
            return cls(value)
        if isinstance(value, str):
            return cls({default_lang: value})
        return None

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema

        def validate(value):
            if isinstance(value, cls):
                return value
            if isinstance(value, dict):
                return cls(value)
            if isinstance(value, str):
                return cls({"_": value})
            raise ValueError(f"Cannot convert {type(value)} to MultiLangText")

        def serialize(value):
            if isinstance(value, cls):
                return value._values
            return value

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj, handler):
        return {
            "type": "object",
            "description": (
                "Multilingual text as {language_code: text}. "
                "A plain string without language info uses key '_'."
            ),
            "additionalProperties": {"type": "string"},
        }


class Identifier(BaseModel):
    """A single identifier in a named scheme."""

    model_config = ConfigDict(frozen=True)

    scheme: str
    value: str


class Identifiers:
    """Collection of identifiers for an entity, with lookup by scheme."""

    __slots__ = ("_ids",)

    def __init__(self, ids: list[Identifier] | None = None) -> None:
        object.__setattr__(self, "_ids", list(ids) if ids else [])

    def get(self, scheme: str) -> str | None:
        for ident in self._ids:
            if ident.scheme == scheme:
                return ident.value
        return None

    def get_all(self, scheme: str) -> list[str]:
        return [ident.value for ident in self._ids if ident.scheme == scheme]

    @property
    def schemes(self) -> list[str]:
        seen = []
        for ident in self._ids:
            if ident.scheme not in seen:
                seen.append(ident.scheme)
        return seen

    def add(self, scheme: str, value: str) -> None:
        self._ids.append(Identifier(scheme=scheme, value=value))

    def __iter__(self) -> Iterator[Identifier]:
        return iter(self._ids)

    def __len__(self) -> int:
        return len(self._ids)

    def __bool__(self) -> bool:
        return bool(self._ids)

    def __repr__(self) -> str:
        return f"Identifiers({self._ids!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Identifiers):
            return self._ids == other._ids
        return NotImplemented

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema

        def validate(value):
            if isinstance(value, cls):
                return value
            if isinstance(value, list):
                ids = [
                    Identifier(**item) if isinstance(item, dict) else item
                    for item in value
                ]
                return cls(ids)
            raise ValueError(f"Cannot convert {type(value)} to Identifiers")

        def serialize(value):
            if isinstance(value, cls):
                return [ident.model_dump() for ident in value._ids]
            return value

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj, handler):
        return {
            "type": "array",
            "description": "Collection of identifiers, each with a scheme and value.",
            "items": {
                "type": "object",
                "properties": {
                    "scheme": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["scheme", "value"],
            },
        }


class Entity(BaseModel):
    """Base class for all entities.

    Provides multi-scheme identifiers and ``extra="allow"`` for domain-specific
    attributes. Core fields are declared on subclasses. Domain-specific fields
    are passed as extra kwargs and accessible directly on the instance.

    Source metadata is stored in ``_raw`` (PrivateAttr, excluded from serialization).

    Configuration:

    - ``extra="allow"``: accepts fields beyond those declared on the model.
      Case-specific and adapter-provided attributes are stored as extra
      fields and accessible directly on the instance (e.g., ``proc.procedure_type``).
    - ``validate_assignment=True``: field values are validated when set after
      construction, not just during ``__init__``.
    - ``arbitrary_types_allowed=True``: permits non-standard types like
      ``MultiLangText`` and ``Identifiers`` as field types.

    Access patterns:

    ```python
    entity.title                # core field (declared)
    entity.procedure_type       # domain-specific (extra)
    entity.model_fields         # Pydantic: declared fields
    entity.model_extra          # Pydantic: extra fields as dict
    entity._raw                 # source metadata (excluded from serialization)
    ```
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
    )

    identifiers: Identifiers = Field(
        default_factory=Identifiers,
        description="Multi-scheme identifiers for this entity (e.g., CELEX, ELI, Cellar, etc. in the EU case).",
    )
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)
