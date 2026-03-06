# Base Models

API reference for the base model classes. Case-specific models (like [EU Models](eu-models.md)) inherit from these and add domain fields. For a conceptual overview, see the [Model Guide](models-guide.md).

## Entity

The abstract base class all models inherit from. Provides multi-scheme identifiers, source metadata storage (`_raw`), and `extra="allow"` for domain-specific attributes.

### Overview

::: openstage.models.core.Entity
    options:
      members: false

### Fields

::: openstage.models.core.Entity
    options:
      show_bases: false

## Legislative models

The three substantive model classes representing a legislative process.

### Procedure

#### Overview

::: openstage.models.procedure.Procedure
    options:
      members: false

#### Fields and properties

::: openstage.models.procedure.Procedure
    options:
      show_bases: false

### Event

#### Overview

::: openstage.models.event.Event
    options:
      members: false

#### Fields

::: openstage.models.event.Event
    options:
      show_bases: false

### Document

#### Overview

::: openstage.models.document.Document
    options:
      members: false

#### Fields

::: openstage.models.document.Document
    options:
      show_bases: false

## Data types

Types used as fields throughout the legislative models.

### MultiLangText

::: openstage.models.core.MultiLangText

### Identifiers

::: openstage.models.core.Identifiers

### Identifier

::: openstage.models.core.Identifier

### Raw metadata (_raw)

The `_raw` private attribute on every entity stores source metadata that does not belong in the typed model. It is excluded from `model_dump()` and serialization.

```python
proc._raw["_rdf_types"]     # Original RDF type URIs
proc._raw["_same_as"]       # owl:sameAs alias URIs
proc._raw["_raw_triples"]   # Unconsumed RDF triples
```

## Field metadata and codebooks

Case models use field metadata annotations and codebook extraction to document their domain-specific properties. See [Fields and Codebooks](fields-codebook.md).
