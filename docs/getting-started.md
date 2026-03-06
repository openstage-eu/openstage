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
import json
from openstage.models.eu import EUProcedure

# Load procedures from a published dataset
with open("openstage_procedures_v1.json") as f:
    data = json.load(f)

procedures = [EUProcedure.model_validate(d) for d in data]

proc = procedures[0]
proc.title["en"]                    # "Regulation on ..."
proc.title.preferred()              # Best available language (en > fr > de > _ > first)
proc.identifiers.get("celex")       # "32016R0679"
proc.events                         # List of EUEvent objects
proc.events[0].documents            # List of EUDocument objects
```

*Dataset reader is under development. See [Models](base-models.md) for details on working with the data types.*

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
