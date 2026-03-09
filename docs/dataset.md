# Datasets

openstage provides two classes for working with collections of procedures: `ProcedureList` for in-memory analytics and `Dataset` for loading and saving packaged dataset files.

## ProcedureList

A list-like container for procedures with filtering and cross-procedure analytics.

```python
from openstage.collections import ProcedureList

pl = ProcedureList(procedures)
```

### List interface

`ProcedureList` supports standard list operations:

```python
len(pl)                     # Number of procedures
pl[0]                       # Access by index (returns Procedure)
pl[1:5]                     # Slice (returns new ProcedureList)
proc in pl                  # Membership test
for p in pl:                # Iteration
    ...
pl.append(proc)             # Add one
pl.extend(more_procs)       # Add many
```

### Filtering

All filter methods return a new `ProcedureList`:

```python
# Custom predicate
olp_with_docs = pl.filter(lambda p: p.procedure_type == "OLP" and p.get_all_documents())

# By status (adopted, ongoing, withdrawn)
adopted = pl.by_status("adopted")

# By procedure type (EU-specific extra field)
olp = pl.by_type("OLP")

# By start date range (inclusive)
recent = pl.started_between("2020-01-01", "2024-12-31")
```

### Cross-procedure analytics

```python
# Procedures that were open (started, not yet adopted or withdrawn) at a date
open_procs = pl.open_at("2024-06-01")

# Count of open procedures at a date
count = pl.backlog_at("2024-06-01")

# Backlog over a series of dates
series = pl.backlog_series(["2020-01-01", "2021-01-01", "2022-01-01"])
# [("2020-01-01", 412), ("2021-01-01", 438), ...]

# Earliest and latest start dates
earliest, latest = pl.date_range

# Group by any attribute
by_type = pl.group_by(lambda p: p.procedure_type)
# {"OLP": ProcedureList(...), "CNS": ProcedureList(...), ...}
```

#### open_at logic

A procedure is considered open at a given date if all of the following hold:

- It has a `start_date` and that date is on or before the query date.
- It has not yet been adopted (`adoption_date` is `None` or after the query date).
- It has not yet been withdrawn (`withdrawal_date` is `None` or after the query date, when available on the procedure class).

### Serialization

```python
# Serialize all procedures to dicts (via model_dump)
dicts = pl.to_dicts()
```

### Standalone functions

The most common operations are also available as standalone functions that accept any iterable of procedures:

```python
from openstage.collections import open_at, backlog_at, filter_procedures

open_procs = open_at(procedures, "2024-06-01")
count = backlog_at(procedures, "2024-06-01")
filtered = filter_procedures(procedures, lambda p: p.status == "adopted")
```

## Dataset

`Dataset` extends `ProcedureList` with metadata and file I/O. It is the standard way to load published openstage datasets and to save procedure collections for sharing.

```python
from openstage.dataset import Dataset
```

### Loading a dataset

```python
# From a directory
ds = Dataset.load("path/to/dataset/")

# From a ZIP archive
ds = Dataset.load("openstage-eu-2026.02.zip")

# From a single JSON file (procedures.json)
ds = Dataset.load("path/to/procedures.json")
```

`load()` auto-detects the format. It reads `metadata.json` if present and uses the dataset `name` field to resolve the correct procedure class from the registry. If no metadata is found, procedures are loaded as base `Procedure` instances.

You can override the procedure class explicitly:

```python
from openstage.models.eu import EUProcedure

ds = Dataset.load("data.zip", procedure_class=EUProcedure)
```

### Dataset metadata

```python
ds.name                     # Dataset identifier (e.g. "openstage-eu")
ds.version                  # Release period (e.g. "2026.02")
ds.description              # Human-readable title
ds.creation_date            # ISO date string
ds.pipeline_versions        # {"openstage": "0.1.0", "openbasement": "abc1234"}
ds.metadata                 # Any additional metadata as a dict
```

### Saving a dataset

```python
ds = Dataset(
    procedures,
    name="openstage-eu",
    version="2026.02",
    description="EU Procedures Dataset",
    creation_date="2026-03-09",
    pipeline_versions={"openstage": "0.1.0"},
)

# Individual files (one JSON per procedure) in a directory
ds.dump("output/")

# Individual files in a ZIP archive
ds.dump("output.zip")

# Single file (one procedures.json array) in a directory
ds.dump("output/", format="single")

# Single file in a ZIP archive
ds.dump("output.zip", format="single")
```

### Dump modes

The `mode` parameter controls what is included in the output:

- **`mode="clean"`** (default): `model_dump()` output only. Pure model data. The `_raw` private attribute is excluded.
- **`mode="full"`**: `model_dump()` plus the `_raw` dict, added explicitly. Preserves source provenance (RDF types, raw triples). Useful for full-fidelity round-trips.

```python
# Clean output (default)
ds.dump("clean.zip", mode="clean")

# Full output including _raw metadata
ds.dump("full.zip", mode="full")
```

On `load()`, if `_raw` is present in the data, it is restored to the private attribute automatically.

### File layouts

Both formats produce a `metadata.json` alongside the procedure data.

**Individual format** (default):

```
metadata.json
2024_0001_COD.json          # One file per procedure
2024_0002_COD.json          # Filename from procedure_ref identifier
...
```

**Single format**:

```
metadata.json
procedures.json             # JSON array of all procedures
```

In a ZIP archive, the same structure appears inside the archive. On disk, a directory.

### Metadata schema

The canonical metadata written by `dump()`:

```json
{
    "name": "openstage-eu",
    "version": "2026.02",
    "description": "EU Procedures Dataset",
    "creation_date": "2026-03-09",
    "total_procedures": 4521,
    "pipeline_versions": {
        "openstage": "0.1.0",
        "openbasement": "abc1234"
    }
}
```

When loading, unknown metadata keys are stored in `ds.metadata` as a catch-all dict. This makes the loader tolerant of additional fields from other tools.

## Class registry

openstage maintains a registry mapping dataset names to procedure classes. When `Dataset.load()` reads a dataset, it uses the `name` field from metadata to look up the correct class for deserialization.

The EU case is registered automatically on import:

- `"openstage-eu"` maps to `EUProcedure`

To register additional cases:

```python
from openstage.dataset import register_dataset

register_dataset("my-dataset", MyProcedure)
```

If no match is found in the registry and no `procedure_class` is passed to `load()`, a warning is emitted and the base `Procedure` class is used.

## API reference

### ProcedureList

::: openstage.collections.ProcedureList
    options:
      show_bases: false

### Dataset

::: openstage.dataset.Dataset
    options:
      show_bases: false

### Standalone functions

::: openstage.collections.open_at

::: openstage.collections.backlog_at

::: openstage.collections.filter_procedures

### Registry functions

::: openstage.dataset.register_dataset

::: openstage.dataset.resolve_class
