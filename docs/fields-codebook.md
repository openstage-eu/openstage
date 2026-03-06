# Fields and Codebooks

openstage provides a field metadata system for annotating case-specific model properties with structured information: variable types, controlled vocabularies, data source provenance, and human-readable labels. These annotations power codebook generation and soft validation.

## Field metadata system

Case models use factory functions from `openstage.models.fields` to declare fields with rich metadata. Each function produces a Pydantic `FieldInfo` with `x_` prefixed custom annotations in `json_schema_extra`.

```python
from openstage.models.fields import nominal_field, id_field, date_field, text_field

class MyProcedure(Procedure):
    procedure_type: str | None = nominal_field(
        description="Type of legislative procedure.",
        label="Procedure type",
        source="my_source:procedure_type",
        known_values={
            "OLP": "Ordinary Legislative Procedure",
            "CNS": "Consultation procedure",
        },
        missing_means="Procedure type not recorded.",
        default=None,
    )
```

### Factory functions

| Function | Variable type | Use for |
|----------|--------------|---------|
| `text_field()` | text | Semantic human-readable content |
| `nominal_field()` | nominal | Categorical values from a controlled vocabulary |
| `id_field()` | identifier | Structured reference strings (URIs, numbers) |
| `date_field()` | date | ISO 8601 date strings |

### Metadata annotations

Each factory function accepts these parameters, stored as `x_` prefixed keys:

- `x_variable_type` -- one of text, nominal, identifier, date
- `x_label` -- human-readable field label
- `x_source` -- data source provenance (e.g., a CDM property URI)
- `x_known_values` -- controlled vocabulary dict (nominal fields only)
- `x_missing_means` -- what a missing value means substantively

### Soft validation

Fields that declare `x_known_values` are soft-validated on construction via `warn_unknown_values()`. Unknown values produce a `UserWarning` rather than raising an exception, so unexpected data is flagged without blocking processing.

## Codebook extraction

The field metadata embedded in case models can be extracted as a structured codebook for documentation or data dictionaries.

```python
from openstage.models.codebook import extract_codebook, codebook_to_markdown
from openstage.models.eu import EUProcedure

entries = extract_codebook(EUProcedure)
print(codebook_to_markdown(entries))
```

Each codebook entry includes:

- `name` -- field name
- `type` -- JSON Schema type string
- `description` -- field description
- `required` -- whether the field is required
- `inherited_from` -- base class name if inherited, None if own field
- `x_variable_type`, `x_label`, `x_source`, `x_known_values`, `x_missing_means` -- field metadata annotations

`codebook_to_markdown()` renders a field table with an appendix listing controlled vocabularies.

## API reference

### Field helpers

::: openstage.models.fields

### Codebook

::: openstage.models.codebook
