"""
openstage data models

System-agnostic Pydantic models for legislative data. Multilingual text
and multi-scheme identifiers are first-class primitives. Domain-specific
attributes use extra="allow" and are accessible directly on entity instances.
"""

from __future__ import annotations

from .core import (
    MultiLangText,
    Identifier,
    Identifiers,
    Entity,
)
from .document import Document
from .event import Event
from .procedure import Procedure
from .fields import (
    text_field,
    nominal_field,
    id_field,
    date_field,
    warn_unknown_values,
)
from .codebook import extract_codebook, codebook_to_markdown

__all__ = [
    "MultiLangText",
    "Identifier",
    "Identifiers",
    "Entity",
    "Document",
    "Event",
    "Procedure",
    "text_field",
    "nominal_field",
    "id_field",
    "date_field",
    "warn_unknown_values",
    "extract_codebook",
    "codebook_to_markdown",
]
