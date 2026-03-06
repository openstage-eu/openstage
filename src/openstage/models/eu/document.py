"""EU-specific document model."""

from __future__ import annotations

from typing import Any

from openstage.models.document import Document
from openstage.models.core import MultiLangText
from openstage.models.fields import id_field, warn_unknown_values


class EUDocument(Document):
    """A document within an EU legislative process.

    Extends the base Document with known EU-specific fields. Unknown extra
    fields are still accepted via extra="allow" inheritance.
    """

    doc_number: str | None = id_field(
        description="Document number assigned by the issuing institution.",
        label="Document number",
        source="openbasement:eu_document.celex",
        missing_means="No document number in source data.",
        default=None,
    )

    def model_post_init(self, __context: Any) -> None:
        warn_unknown_values(self)

    @classmethod
    def from_openbasement(cls, data: dict) -> EUDocument:
        """Map an openbasement document dict to an EUDocument."""
        from openstage.adapters.eu.procedures import (
            _identifiers_from_uris,
            _build_raw,
            _build_extras,
            _DOCUMENT_CORE_KEYS,
        )

        doc = cls(
            identifiers=_identifiers_from_uris(
                data.get("_uri"), data.get("_same_as")
            ),
            title=MultiLangText.from_value(data.get("title")),
            date=data.get("date"),
            **_build_extras(data, _DOCUMENT_CORE_KEYS),
        )
        doc._raw = _build_raw(data)
        return doc
