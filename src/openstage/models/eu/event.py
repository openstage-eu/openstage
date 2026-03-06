"""EU-specific event model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from openstage.models.event import Event
from openstage.models.core import MultiLangText
from openstage.models.fields import nominal_field, warn_unknown_values

from .document import EUDocument


class EUEvent(Event):
    """An event within an EU legislative process.

    Extends the base Event with known EU-specific fields. The documents list
    uses EUDocument instead of the base Document type.

    Documents are populated from three openbasement sources:

    1. ``documents`` -- entities from ``cdm:event_legal_contains_work``
       (structured RDF entities with URI, title, date, resource type).
    2. ``works`` -- entities from ``cdm:event_contains_work`` (same shape
       as documents, mapped identically).
    3. ``document_reference`` -- literal strings from
       ``cdm:event_legal_document_reference`` (e.g. "COM/2020/319/FINAL").
       These become stub documents with a ``doc_ref`` identifier scheme.

    Sources 1 and 2 may overlap with source 3 for the same underlying
    document. Deduplication happens later when full document metadata
    (from separate per-document RDF extraction) is available.
    """

    documents: list[EUDocument] = Field(
        default_factory=list,
        description="Documents associated with this EU event.",
    )

    initiated_by_institution: str | None = nominal_field(
        description="Institution that initiated this event.",
        label="Initiating institution",
        source="openbasement:eu_procedure.initiated_by_institution",
        known_values={
            "COM": "European Commission",
            "EP": "European Parliament",
            "COUNCIL": "Council of the European Union",
            "CSL": "Council of the European Union",
            "ECB": "European Central Bank",
            "EESC": "European Economic and Social Committee",
            "COR": "European Committee of the Regions",
        },
        missing_means="No initiating institution recorded.",
        default=None,
    )

    occurs_in_phase: str | None = nominal_field(
        description="Legislative phase in which this event occurs.",
        label="Legislative phase",
        source="openbasement:eu_procedure.occurs_in_phase",
        known_values={
            "FIRST_READING": "First reading",
            "SECOND_READING": "Second reading",
            "THIRD_READING": "Third reading",
            "CONCILIATION": "Conciliation procedure",
        },
        missing_means="Phase not specified in source data.",
        default=None,
    )

    def model_post_init(self, __context: Any) -> None:
        warn_unknown_values(self)

    @classmethod
    def from_openbasement(cls, data: dict) -> EUEvent:
        """Map an openbasement event dict to an EUEvent."""
        from openstage.adapters.eu.procedures import (
            _identifiers_from_uris,
            _build_raw,
            _build_extras,
            _EVENT_CORE_KEYS,
            _identifiers_from_reference,
        )

        documents = [
            EUDocument.from_openbasement(d) for d in data.get("documents", [])
        ]
        documents.extend(
            EUDocument.from_openbasement(w) for w in data.get("works", [])
        )
        documents.extend(
            EUDocument(identifiers=_identifiers_from_reference(ref))
            for ref in data.get("document_reference", [])
        )

        event = cls(
            identifiers=_identifiers_from_uris(
                data.get("_uri"), data.get("_same_as")
            ),
            date=data.get("date"),
            title=MultiLangText.from_value(data.get("title")),
            type=data.get("type_code"),
            documents=documents,
            **_build_extras(data, _EVENT_CORE_KEYS),
        )
        event._raw = _build_raw(data)
        return event
