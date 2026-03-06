"""Document model for legislative data."""

from __future__ import annotations

from pydantic import Field

from .core import Entity, MultiLangText


class Document(Entity):
    """A document within a legislative process.

    Core fields are system-agnostic (title, date). Domain-specific
    attributes are accessible directly as extra fields.
    """

    title: MultiLangText | None = Field(
        default=None,
        description="Document title, potentially in multiple languages.",
        json_schema_extra={"x_variable_type": "text"},
    )
    date: str | None = Field(
        default=None,
        description="Date associated with this document (ISO 8601).",
        json_schema_extra={"x_variable_type": "date"},
    )
