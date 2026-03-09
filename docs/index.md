# openstage

Typed Python models for legislative data. `openstage` provides a common data model for procedures, events, and documents with built-in support for multilingual text and multi-scheme identifiers.

Note: `openstage` is both the project name and the Python package name (`import openstage`).

## Guiding principle

Legislative data across systems shares common structures: procedures contain events, events produce documents, text appears in multiple languages, and entities carry identifiers from several naming schemes. `openstage` captures these patterns in typed Pydantic models that work across legislative systems.

The EU is the primary implemented case. EU-specific models extend the base types with typed fields for procedure types, legislative phases, institutional actors, and other domain concepts drawn from the Common Data Model (CDM).

## Usage

**Most researchers** download a pre-compiled dataset and load it directly into typed models. No collection, no parsing, no extra dependencies.

**Power users** can collect raw data from EUR-Lex and Cellar using [openstage-infrastructure](https://github.com/openstage-eu/openstage-infrastructure), parse it with [openbasement](https://openstage-eu.github.io/openbasement/), and map the results into the same typed models using the adapter layer.

Both paths produce the same model objects.

## Package layers

| Layer | What it does | Dependencies |
|-------|-------------|--------------|
| `models/` | Typed Pydantic models with multilingual text and multi-scheme identifiers | pydantic |
| `models/eu/` | EU case models extending base types with domain-specific fields | pydantic |
| `adapters/` | Map external data (openbasement dicts) into models | pydantic |
| `collections` | `ProcedureList` for filtering and cross-procedure analytics | -- |
| `dataset` | `Dataset` for loading and saving packaged procedure collections | -- |

## Part of the openstage project

- **openstage** (this package): Data models and adapters
- **[openbasement](https://openstage-eu.github.io/openbasement/)**: Template-based RDF extraction from EU Cellar data
- **openstage-infrastructure**: Workflow orchestration, storage, and publishing

## Next steps

- [Getting started](getting-started.md): Install, load data, explore models.
- [Base models](base-models.md): Entity hierarchy, multilingual text, identifiers.
- [EU models](eu-models.md): EU-specific fields, controlled vocabularies, codebook.
- [Datasets](dataset.md): Loading, saving, filtering, and analyzing procedure collections.
- [Fields and codebooks](fields-codebook.md): Field metadata system and codebook generation.
