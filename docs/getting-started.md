# Getting Started

## Installation

`openstage` is not yet published on PyPI. Install directly from GitHub:

```bash
# Models, adapters, dataset reading
pip install openstage @ git+https://github.com/openstage-eu/openstage.git
```

## Loading a published dataset

The primary use case. Download a pre-compiled openstage dataset and load it into typed models:

```python
from openstage.dataset import Dataset

# Load a dataset from a directory or ZIP archive
ds = Dataset.load("openstage-eu-2026.02.zip")

# Dataset metadata
ds.name                             # "openstage-eu"
ds.version                          # "2026.02"
len(ds)                             # Number of procedures

# Access individual procedures
proc = ds[0]
proc.title["en"]                    # "Regulation on ..."
proc.title.preferred()              # Best available language (en > fr > de > _ > first)
proc.identifiers.get("celex")       # "32016R0679"
proc.events                         # List of EUEvent objects
proc.events[0].documents            # List of EUDocument objects
```

The `Dataset` class auto-detects the file format and resolves the correct procedure class from dataset metadata. See [Datasets](dataset.md) for the full API.

## Working with collections

`Dataset` inherits from `ProcedureList`, so all collection methods are available directly:

```python
# Filter by status or type
adopted = ds.by_status("adopted")
olp = ds.by_type("OLP")

# Procedures open at a specific date
open_2024 = ds.open_at("2024-06-01")

# Group by any attribute
by_type = ds.group_by(lambda p: p.procedure_type)
```

See [Datasets](dataset.md) for the full collection and I/O API.

## Collecting raw data (power users)

Data collection (downloading from EUR-Lex and Cellar) lives in [openstage-infrastructure](https://github.com/openstage-eu/openstage-infrastructure). See that repository for collection tools and workflow orchestration.

## From parsed data to typed models

Combining `openstage` with [openbasement](https://openstage-eu.github.io/openbasement/) for the path from parsed RDF to typed models:

```python
# 1. Parse RDF with openbasement (given raw RDF bytes)
from rdflib import Graph
from openbasement import extract
g = Graph().parse(data=rdf_bytes, format="xml")
results = extract(g, template="eu_procedure")

# 2. Map into typed EU models
from openstage.models.eu import EUProcedure
proc = EUProcedure.from_openbasement(results[0])

proc.title["en"]                    # Multilingual title
proc.identifiers.get("celex")       # CELEX identifier
proc.procedure_type                 # EU-specific field (e.g. "OLP")
```

`openbasement` is a soft dependency. It is not imported by `openstage`. The adapter expects plain dicts in the shape that openbasement produces.
