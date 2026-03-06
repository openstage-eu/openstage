"""Procedure model for legislative data."""

from __future__ import annotations

import warnings

from pydantic import Field

from .core import Entity, MultiLangText
from .document import Document
from .event import Event

# Properties that concrete subclasses should override with domain-specific
# logic. A warning is emitted at class definition time if they are not.
_INTERFACE_PROPERTIES = ("adoption_event", "status")


class Procedure(Entity):
    """A legislative procedure.

    Top-level container holding events and metadata about a legislative
    process. Documents live under events, reflecting their role in
    specific stages of the procedure.

    Core fields are system-agnostic. Domain-specific attributes are
    accessible directly as extra fields.

    Subclasses for specific legislative systems (EU, US, etc.) should
    override the following properties with domain-specific logic:

    - ``start_event`` -- the event that initiated the procedure
    - ``adoption_event`` -- the event where the text was formally adopted
    - ``status`` -- procedure status (ongoing, adopted, withdrawn, etc.)

    Base defaults use chronological heuristics where possible and return
    None where domain knowledge is required.
    """

    title: MultiLangText | None = Field(
        default=None,
        description="Procedure title, potentially in multiple languages.",
        json_schema_extra={"x_variable_type": "text"},
    )
    events: list[Event] = Field(
        default_factory=list,
        description="Events in this legislative procedure.",
    )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for prop_name in _INTERFACE_PROPERTIES:
            if prop_name not in cls.__dict__:
                warnings.warn(
                    f"{cls.__name__} does not override '{prop_name}'. "
                    f"The base Procedure default will be used. "
                    f"Consider implementing domain-specific logic.",
                    stacklevel=2,
                )

    # -- Researcher-facing interface ------------------------------------------

    @property
    def start_event(self) -> Event | None:
        """Event that initiated this procedure.

        Base default: earliest event by date. Subclasses should override
        to identify the domain-specific start event (e.g. proposal event).
        """
        dated = [e for e in self.events if e.date]
        return min(dated, key=lambda e: e.date) if dated else None

    @property
    def start_date(self) -> str | None:
        """Date when this procedure started."""
        event = self.start_event
        return event.date if event else None

    @property
    def adoption_event(self) -> Event | None:
        """Event where the legislative text was formally adopted.

        Returns None on the base model. Subclasses should override to
        identify the domain-specific adoption event (e.g. formal Council
        adoption in the EU, presidential signature in the US).
        """
        return None

    @property
    def adoption_date(self) -> str | None:
        """Date when the legislative text was adopted, or None."""
        event = self.adoption_event
        return event.date if event else None

    @property
    def status(self) -> str | None:
        """Procedure status.

        Base default: "adopted" if an adoption event exists, "ongoing"
        otherwise. Subclasses should override with domain-specific logic
        (e.g. distinguishing withdrawn, rejected, lapsed procedures).
        """
        if self.adoption_event is not None:
            return "adopted"
        return "ongoing" if self.events else None

    # -- Utility methods ------------------------------------------------------

    def get_all_documents(self) -> list[Document]:
        """Collect all documents from all events in this procedure."""
        docs = []
        for event in self.events:
            docs.extend(event.documents)
        return docs
