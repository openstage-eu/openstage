"""EU-specific procedure model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from openstage.models.procedure import Procedure
from openstage.models.event import Event
from openstage.models.core import MultiLangText
from openstage.models.fields import (
    nominal_field,
    id_field,
    date_field,
    warn_unknown_values,
)

from .event import EUEvent

# Event type codes that indicate the Commission's initial proposal.
_START_EVENT_TYPES = {
    "ADP_byCOM",
    "Adoption par Commission",
    "ADP_PROPLEG_byCOM",
}

# Event type codes that indicate formal adoption of the legislative text.
_ADOPTION_EVENT_TYPES = {
    "ADP_FRM_byCONSIL",
    "Adoption formelle par Conseil",
    "SIGN_byEP_CONSIL",
    "Signature par le Parlement européen et le Conseil",
}

# Event type codes that indicate the procedure was withdrawn.
_WITHDRAWAL_EVENT_TYPES = {
    "Retrait par Commission",
}


class EUProcedure(Procedure):
    """An EU legislative procedure with typed domain-specific fields.

    Extends the base Procedure with known EU fields that carry rich metadata
    (variable type, controlled vocabularies, data source provenance). The
    events list uses the EU-specific subtype.

    Overrides the base ``start_event``, ``adoption_event``, and ``status``
    properties with EU-specific event type matching.
    """

    events: list[EUEvent] = Field(
        default_factory=list,
        description="Events in this EU legislative procedure.",
    )

    procedure_type: str | None = nominal_field(
        description="Type of EU legislative procedure.",
        label="Procedure type",
        source="openbasement:eu_procedure.procedure_type",
        known_values={
            "OLP": "Ordinary Legislative Procedure",
            "CNS": "Consultation procedure",
            "APP": "Consent procedure",
            "NLE": "Non-legislative enactment",
            "BUD": "Budgetary procedure",
            "DIS": "Discharge procedure",
            "RSP": "Resolution procedure",
            "INI": "Own-initiative procedure",
            "DCE": "Delegated act procedure",
            "IMM": "Immunity procedure",
        },
        missing_means="Procedure type not recorded in source data.",
        default=None,
    )

    subject_matters: list[str] = id_field(
        description="EuroVoc subject matter URIs associated with this procedure.",
        label="Subject matters",
        source="openbasement:eu_procedure.subject_matters",
        missing_means="No subject matters recorded.",
        default_factory=list,
    )

    basis_legal: str | None = id_field(
        description="Legal basis URI for this procedure.",
        label="Legal basis",
        source="openbasement:eu_procedure.basis_legal",
        missing_means="No legal basis recorded.",
        default=None,
    )

    year_procedure: str | None = id_field(
        description="Year component of the procedure reference number.",
        label="Procedure year",
        source="openbasement:eu_procedure.year_procedure",
        missing_means="Year not available.",
        default=None,
    )

    number_procedure: str | None = id_field(
        description="Sequence number component of the procedure reference.",
        label="Procedure number",
        source="openbasement:eu_procedure.number_procedure",
        missing_means="Number not available.",
        default=None,
    )

    date: str | None = date_field(
        description="Date associated with this procedure (typically the latest significant event).",
        label="Procedure date",
        source="openbasement:eu_procedure.date",
        missing_means="No date recorded.",
        default=None,
    )

    # -- Interface overrides --------------------------------------------------

    @property
    def start_event(self) -> Event | None:
        """The Commission proposal event that initiated this procedure.

        Looks for known proposal event types. Falls back to the earliest
        event by date if no proposal event is found.
        """
        for event in self.events:
            if event.type in _START_EVENT_TYPES:
                return event
        return super().start_event

    @property
    def adoption_event(self) -> Event | None:
        """The event where the legislative text was formally adopted.

        Looks for formal adoption or signature events. Returns None if
        the procedure has not (yet) been adopted.
        """
        for event in self.events:
            if event.type in _ADOPTION_EVENT_TYPES:
                return event
        return None

    @property
    def withdrawal_event(self) -> Event | None:
        """The event where the procedure was withdrawn by the Commission.

        Returns None if the procedure has not been withdrawn.
        """
        for event in self.events:
            if event.type in _WITHDRAWAL_EVENT_TYPES:
                return event
        return None

    @property
    def withdrawal_date(self) -> str | None:
        """Date when the procedure was withdrawn, or None."""
        event = self.withdrawal_event
        return event.date if event else None

    @property
    def status(self) -> str | None:
        """EU procedure status: adopted, withdrawn, or ongoing."""
        if self.adoption_event is not None:
            return "adopted"
        if self.withdrawal_event is not None:
            return "withdrawn"
        return "ongoing" if self.events else None

    def model_post_init(self, __context: Any) -> None:
        warn_unknown_values(self)

    @classmethod
    def from_openbasement(cls, data: dict) -> EUProcedure:
        """Map an openbasement eu_procedure result to an EUProcedure.

        Core fields (title, date, identifiers) are mapped to typed model
        fields. EU-specific fields with declared metadata become typed
        attributes. Remaining domain-specific fields become extra attributes.
        Source metadata (_rdf_types, _raw_triples) goes to _raw.
        """
        from openstage.adapters.eu.procedures import (
            _identifiers_from_uris,
            _build_raw,
            _build_extras,
            _PROCEDURE_CORE_KEYS,
        )

        events = [EUEvent.from_openbasement(e) for e in data.get("events", [])]

        identifiers = _identifiers_from_uris(data.get("_uri"), data.get("_same_as"))
        ref = data.get("reference")
        if ref:
            identifiers.add("procedure_ref", ref)

        proc = cls(
            identifiers=identifiers,
            title=MultiLangText.from_value(data.get("title")),
            events=events,
            **_build_extras(data, _PROCEDURE_CORE_KEYS),
        )
        proc._raw = _build_raw(data)
        return proc
