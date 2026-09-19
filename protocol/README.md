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

## Federation invariants

- An instance can publish an envelope without surrendering ownership of its records.
- Stable identifiers survive export and federation.
- Source-instance metadata travels with federated results.
- Tombstones travel with envelopes and prevent withdrawn records from being silently resurrected.
- Private, community, trusted-custodian and sealed material is not exposed by a public federated query unless the caller explicitly supplies the permitted visibility set.
- Identical replicas of a stable object are deduplicated deterministically.
- Divergent content under the same stable identifier is surfaced as a conflict rather than silently selecting a winner.
- Relationships are only traversed between records present in the federated query set; federation does not invent edges.
- Federation is additive: imported provenance, revisions and permissions remain distinguishable from the local instance.

## Historical exploration

The historical exploration contract can surface records, archive sources, Memory Albums, media, relationships, contradictions and timelines for a place/time query.

The federated historical exploration contract applies the same query across multiple independent instances. A place can therefore become a distributed time machine without becoming a centralized database.

The JSON Schema files in this directory are machine-readable contracts. Compatibility is expanded through tested protocol versions rather than speculative fields.


## Discovery and incremental sync

An independent instance can publish a discovery manifest containing its stable instance ID, protocol version, capabilities, public visibility classes, record-type coverage and current change cursor. Endpoint descriptors are metadata only; the protocol does not require one transport.

A peer can issue an incremental sync request with its last cursor. The instance returns only change envelopes after that cursor, together with the next cursor and a has_more signal. Change envelopes may contain new or revised records, albums, media, sources, relationships, source links and tombstones.

The cursor belongs to the source instance. It is not a global clock and does not replace provenance timestamps. A peer should persist the cursor only after successfully processing the returned changes.
