# Protocol

The protocol defines portable records independently of storage, interface and AI provider.

## Contract invariants

- Every record has a stable moh: identifier.
- Original content is preserved as submitted.
- Provenance identifies the contributor and creation time.
- Epistemic status describes what kind of knowledge the record represents.
- Revisions point backward rather than erasing history.
- Relationships point to other stable record identifiers.
- Derived material identifies its source and transformation.
- Permissions are metadata carried with the record.
- AI output is never implicitly treated as source material.

The JSON Schema in this directory is the first machine-readable contract. It is intentionally small; compatibility will be expanded through tested protocol versions rather than speculative fields.
