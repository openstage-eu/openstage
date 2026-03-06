"""Map openbasement EU procedure dicts into openstage models.

openbasement produces flat dicts with _ prefixed metadata keys, multilingual
text as {lang: text} dicts, and nested entity lists for events/documents.
This module maps that output into typed Procedure/Event/Document models.
"""

from __future__ import annotations

import re
from typing import Any

from openstage.models import (
    MultiLangText,
    Identifiers,
    Procedure,
    Event,
    Document,
)

# URI pattern -> identifier scheme
_URI_SCHEMES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"/resource/cellar/"), "cellar"),
    (re.compile(r"/resource/celex/"), "celex"),
    (re.compile(r"/resource/procedure/"), "procedure_ref"),
    (re.compile(r"/resource/pegase/"), "pegase"),
    (re.compile(r"/eli/"), "eli"),
]


def _scheme_from_uri(uri: str) -> str:
    """Determine the identifier scheme from a Cellar URI pattern."""
    for pattern, scheme in _URI_SCHEMES:
        if pattern.search(uri):
            return scheme
    return "uri"


def _value_from_uri(uri: str) -> str:
    """Extract the identifier value (last path segment) from a URI."""
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _identifiers_from_uris(
    uri: str | None, same_as: list[str] | None
) -> Identifiers:
    """Build an Identifiers collection from a primary URI and owl:sameAs list."""
    ids = Identifiers()
    all_uris = []
    if uri:
        all_uris.append(uri)
    if same_as:
        all_uris.extend(same_as)
    for u in all_uris:
        scheme = _scheme_from_uri(u)
        value = _value_from_uri(u)
        ids.add(scheme, value)
    return ids


# Keys that are mapped to typed model fields or handled specially.
# Everything else becomes extra fields on the model.
_PROCEDURE_CORE_KEYS = {
    "_uri", "_same_as", "_rdf_types", "_raw_triples",
    "title", "reference",
    "events", "documents",
}

_EVENT_CORE_KEYS = {
    "_uri", "_same_as", "_rdf_types", "_raw_triples",
    "title", "date", "type_code",
    "documents", "works", "document_reference",
}

_DOCUMENT_CORE_KEYS = {
    "_uri", "_same_as", "_rdf_types", "_raw_triples",
    "title", "date",
}


def _build_raw(data: dict) -> dict[str, Any]:
    """Collect source metadata into the raw dict."""
    raw = {}
    if "_rdf_types" in data:
        raw["_rdf_types"] = data["_rdf_types"]
    if "_raw_triples" in data:
        raw["_raw_triples"] = data["_raw_triples"]
    return raw


def _build_extras(data: dict, core_keys: set[str]) -> dict[str, Any]:
    """Collect all non-core, non-metadata keys as extra fields."""
    extra = {}
    for key, value in data.items():
        if key not in core_keys and not key.startswith("_"):
            extra[key] = value
    return extra


def _document_from_openbasement(data: dict) -> Document:
    """Map an openbasement document dict to a Document."""
    doc = Document(
        identifiers=_identifiers_from_uris(data.get("_uri"), data.get("_same_as")),
        title=MultiLangText.from_value(data.get("title")),
        date=data.get("date"),
        **_build_extras(data, _DOCUMENT_CORE_KEYS),
    )
    doc._raw = _build_raw(data)
    return doc


def _identifiers_from_reference(ref: str) -> Identifiers:
    """Build an Identifiers collection from a document_reference string.

    Document references are human-readable codes (e.g. "COM/2020/319/FINAL",
    "ST 5413 2021 COR 1") extracted from cdm:event_legal_document_reference.
    They identify a document but carry no structured metadata. The reference
    is stored under the "doc_ref" scheme. Deduplication with URI-based
    documents happens later when full document metadata is available.
    """
    ids = Identifiers()
    ids.add("doc_ref", ref)
    return ids


def _event_from_openbasement(data: dict) -> Event:
    """Map an openbasement event dict to an Event."""
    documents = [
        _document_from_openbasement(d) for d in data.get("documents", [])
    ]
    # works are also documents in openbasement output
    documents.extend(
        _document_from_openbasement(w) for w in data.get("works", [])
    )
    # document_reference strings become stub documents
    documents.extend(
        Document(identifiers=_identifiers_from_reference(ref))
        for ref in data.get("document_reference", [])
    )

    event = Event(
        identifiers=_identifiers_from_uris(data.get("_uri"), data.get("_same_as")),
        date=data.get("date"),
        title=MultiLangText.from_value(data.get("title")),
        type=data.get("type_code"),
        documents=documents,
        **_build_extras(data, _EVENT_CORE_KEYS),
    )
    event._raw = _build_raw(data)
    return event


def procedure_from_openbasement(data: dict) -> Procedure:
    """Map an openbasement eu_procedure result to a Procedure.

    Delegates to EUProcedure.from_openbasement() which returns typed EU models.
    EUProcedure is a subclass of Procedure, so this is backward compatible.
    """
    from openstage.models.eu import EUProcedure

    return EUProcedure.from_openbasement(data)
