```python
from openstage.models.eu import EUProcedure

# From openbasement extraction results
proc = EUProcedure.from_openbasement(data)

# Base fields (inherited)
proc.title["en"]                    # Multilingual title
proc.identifiers.get("celex")       # CELEX identifier
proc.events                         # List of EUEvent objects
proc.get_all_documents()            # All documents across all events

# EU-specific fields
proc.procedure_type                 # "OLP", "CNS", etc.
proc.subject_matters                # List of EuroVoc URIs
proc.basis_legal                    # Legal basis URI
proc.year_procedure                 # "2021"
proc.number_procedure               # "0381"
proc.date                           # Procedure date

# Researcher interface (EU-specific overrides)
proc.start_event                    # Commission proposal event
proc.start_date                     # Date of proposal
proc.adoption_event                 # Formal adoption event (or None)
proc.adoption_date                  # Date of adoption (or None)
proc.status                         # "adopted", "withdrawn", or "ongoing"
```
