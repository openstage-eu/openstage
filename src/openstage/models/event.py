"""Event model for legislative data."""

from __future__ import annotations

from pydantic import Field

from .core import Entity, MultiLangText
from .document import Document


class Event(Entity):
    """An event within a legislative process.

    Core fields are system-agnostic (date, title, type, documents).
    Domain-specific attributes are accessible directly as extra fields.
    """

    date: str | None = Field(
        default=None,
        description="Date when this event occurred (ISO 8601).",
        json_schema_extra={"x_variable_type": "date"},
    )
    title: MultiLangText | None = Field(
        default=None,
        description="Event title, potentially in multiple languages.",
        json_schema_extra={"x_variable_type": "text"},
    )
    type: str | None = Field(
        default=None,
        description="Event type code.",
        json_schema_extra={"x_variable_type": "nominal"},
    )
    documents: list[Document] = Field(
        default_factory=list,
        description="Documents associated with this event.",
    )
