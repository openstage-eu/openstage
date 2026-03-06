"""Field metadata helpers for openstage models.

Provides factory functions that return Pydantic FieldInfo with structured
metadata using x_ prefixed custom annotations (JSON Schema convention for
custom extensions). These annotations power codebook generation and soft
validation of controlled vocabularies.

Variable types:

- **text**: semantic human-readable content, may be multilingual
- **nominal**: categorical value from a controlled vocabulary
- **identifier**: structured reference string (URIs, CELEX numbers)
- **date**: ISO 8601 date string
"""

from __future__ import annotations

import warnings
from typing import Any

from pydantic import Field
from pydantic.fields import FieldInfo


def _build_json_schema_extra(
    variable_type: str,
    label: str | None = None,
    source: str | None = None,
    known_values: dict[str, str] | None = None,
    missing_means: str | None = None,
) -> dict[str, Any]:
    """Build the json_schema_extra dict with x_ prefixed keys."""
    extra: dict[str, Any] = {"x_variable_type": variable_type}
    if label is not None:
        extra["x_label"] = label
    if source is not None:
        extra["x_source"] = source
    if known_values is not None:
        extra["x_known_values"] = known_values
    if missing_means is not None:
        extra["x_missing_means"] = missing_means
    return extra


def text_field(
    description: str,
    label: str | None = None,
    source: str | None = None,
    missing_means: str | None = None,
    **kwargs: Any,
) -> FieldInfo:
    """Field for semantic human-readable content."""
    return Field(
        description=description,
        json_schema_extra=_build_json_schema_extra(
            "text", label=label, source=source, missing_means=missing_means,
        ),
        **kwargs,
    )


def nominal_field(
    description: str,
    label: str | None = None,
    source: str | None = None,
    known_values: dict[str, str] | None = None,
    missing_means: str | None = None,
    **kwargs: Any,
) -> FieldInfo:
    """Field for categorical values from a controlled vocabulary."""
    return Field(
        description=description,
        json_schema_extra=_build_json_schema_extra(
            "nominal",
            label=label,
            source=source,
            known_values=known_values,
            missing_means=missing_means,
        ),
        **kwargs,
    )


def id_field(
    description: str,
    label: str | None = None,
    source: str | None = None,
    missing_means: str | None = None,
    **kwargs: Any,
) -> FieldInfo:
    """Field for structured reference strings (URIs, CELEX numbers)."""
    return Field(
        description=description,
        json_schema_extra=_build_json_schema_extra(
            "identifier", label=label, source=source, missing_means=missing_means,
        ),
        **kwargs,
    )


def date_field(
    description: str,
    label: str | None = None,
    source: str | None = None,
    missing_means: str | None = None,
    **kwargs: Any,
) -> FieldInfo:
    """Field for ISO 8601 date strings."""
    return Field(
        description=description,
        json_schema_extra=_build_json_schema_extra(
            "date", label=label, source=source, missing_means=missing_means,
        ),
        **kwargs,
    )


def warn_unknown_values(instance: Any) -> None:
    """Emit warnings for nominal field values not in their known_values set.

    Inspects the model's declared fields for x_known_values metadata.
    If a field has a value that is not in the known set, emits a
    UserWarning. Never raises exceptions.
    """
    for field_name, field_info in type(instance).model_fields.items():
        schema_extra = field_info.json_schema_extra
        if not isinstance(schema_extra, dict):
            continue
        known = schema_extra.get("x_known_values")
        if known is None:
            continue

        value = getattr(instance, field_name, None)
        if value is None:
            continue

        # Handle both single values and lists
        values = value if isinstance(value, list) else [value]
        for v in values:
            if isinstance(v, str) and v not in known:
                warnings.warn(
                    f"{type(instance).__name__}.{field_name}: "
                    f"unknown value {v!r} (known: {sorted(known)})",
                    UserWarning,
                    stacklevel=2,
                )
