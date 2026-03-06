"""Codebook extraction from openstage model schemas.

Walks Pydantic model_json_schema() output and produces a flat list of field
descriptors with x_ metadata annotations. Inherited fields are marked with
their source model so documentation generators can link back.
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel


def extract_codebook(model_class: Type[BaseModel]) -> list[dict[str, Any]]:
    """Extract codebook entries from a Pydantic model class.

    Returns a list of dicts, one per field, with keys:

    - ``name``: field name
    - ``type``: JSON Schema type string
    - ``description``: field description
    - ``required``: whether the field is required
    - ``inherited_from``: base class name if inherited, None if own field
    - ``x_variable_type``: variable type annotation (if present)
    - ``x_label``: human-readable label (if present)
    - ``x_source``: data source annotation (if present)
    - ``x_known_values``: controlled vocabulary dict (if present)
    - ``x_missing_means``: meaning of missing values (if present)
    """
    schema = model_class.model_json_schema()
    required_fields = set(schema.get("required", []))
    properties = schema.get("properties", {})

    # Determine which fields are inherited vs own
    own_fields = set(model_class.__annotations__.keys())
    inherited_map = _build_inheritance_map(model_class)

    entries = []
    for field_name, field_schema in properties.items():
        # Resolve anyOf (used by Pydantic for Optional types)
        resolved = _resolve_schema(field_schema, schema)

        entry: dict[str, Any] = {
            "name": field_name,
            "type": _extract_type(resolved),
            "description": resolved.get("description"),
            "required": field_name in required_fields,
            "inherited_from": inherited_map.get(field_name),
        }

        # Copy x_ annotations
        for key in ("x_variable_type", "x_label", "x_source",
                     "x_known_values", "x_missing_means"):
            if key in resolved:
                entry[key] = resolved[key]

        entries.append(entry)

    return entries


def _build_inheritance_map(model_class: Type[BaseModel]) -> dict[str, str]:
    """Map field names to the base class that first declares them."""
    result: dict[str, str] = {}
    own = set(model_class.__annotations__.keys())

    for base in model_class.__mro__[1:]:
        if base is BaseModel or base is object:
            continue
        base_annotations = getattr(base, "__annotations__", {})
        for field_name in base_annotations:
            if field_name not in own and field_name not in result:
                result[field_name] = base.__name__

    return result


def _resolve_schema(
    field_schema: dict[str, Any], root_schema: dict[str, Any]
) -> dict[str, Any]:
    """Resolve $ref and anyOf to get the actual field schema with metadata."""
    # Handle $ref
    if "$ref" in field_schema:
        ref_path = field_schema["$ref"]
        ref_name = ref_path.rsplit("/", 1)[-1]
        defs = root_schema.get("$defs", {})
        resolved = dict(defs.get(ref_name, {}))
        # Merge top-level annotations back (description, x_* etc.)
        for key, value in field_schema.items():
            if key != "$ref":
                resolved[key] = value
        return resolved

    # Handle anyOf (Pydantic uses this for Optional[T])
    if "anyOf" in field_schema:
        for option in field_schema["anyOf"]:
            if option.get("type") != "null":
                resolved = dict(option)
                # If the non-null option is a $ref, resolve it
                if "$ref" in resolved:
                    resolved = _resolve_schema(resolved, root_schema)
                # Merge top-level annotations
                for key, value in field_schema.items():
                    if key != "anyOf":
                        resolved[key] = value
                return resolved

    return field_schema


def _extract_type(schema: dict[str, Any]) -> str:
    """Extract a human-readable type string from a JSON Schema fragment."""
    if "type" in schema:
        t = schema["type"]
        if t == "array" and "items" in schema:
            item_type = _extract_type(schema["items"])
            return f"array[{item_type}]"
        return t
    if "anyOf" in schema:
        types = [_extract_type(opt) for opt in schema["anyOf"]]
        return " | ".join(types)
    return "any"


def codebook_to_markdown(entries: list[dict[str, Any]]) -> str:
    """Render codebook entries as a markdown document.

    Produces a field table followed by an appendix listing controlled
    vocabularies for fields that have ``x_known_values``.
    """
    lines = ["# Codebook", ""]

    # Field table
    lines.append("| Field | Type | Variable | Description | Inherited from |")
    lines.append("|-------|------|----------|-------------|----------------|")

    vocabularies: list[tuple[str, dict[str, str]]] = []

    for entry in entries:
        name = entry["name"]
        type_str = entry.get("type", "")
        var_type = entry.get("x_variable_type", "")
        desc = entry.get("description", "") or ""
        inherited = entry.get("inherited_from", "") or ""

        lines.append(f"| {name} | {type_str} | {var_type} | {desc} | {inherited} |")

        known = entry.get("x_known_values")
        if known:
            vocabularies.append((name, known))

    # Controlled vocabularies appendix
    if vocabularies:
        lines.extend(["", "## Controlled vocabularies", ""])
        for field_name, values in vocabularies:
            lines.append(f"### {field_name}")
            lines.append("")
            lines.append("| Value | Meaning |")
            lines.append("|-------|---------|")
            for value, meaning in sorted(values.items()):
                lines.append(f"| {value} | {meaning} |")
            lines.append("")

    return "\n".join(lines)
