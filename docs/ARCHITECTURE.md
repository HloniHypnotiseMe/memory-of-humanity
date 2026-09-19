# Architecture

## Direction

The project is a protocol first and an application second.

The reference architecture is intended to support independent implementations and federation rather than requiring one central service.

## Layers

### Protocol
Defines durable vocabulary and contracts for record types, identifiers, provenance, epistemic status, relationships, revisions, permissions, evidence, media references, legal-status metadata and federation envelopes.

### Core
Provides deterministic validation and domain logic. Core logic should not require an AI provider, hosted database, cloud vendor or specific interface.

### Preservation
Handles durable references to text, images, audio, video, documents, maps, scans and technical diagrams. Binary storage may vary by implementation; identity and provenance must remain independent of storage location.

### Knowledge
Provides structured representations for people, places, events, objects, stories, practices, technologies and documents. Relationships are first-class data.

### AI
Optional assistance layer. AI outputs are derived records or annotations with their own provenance. They do not overwrite source records.

### Federation
Allows independently operated instances to exchange records and historical objects while retaining stable identifiers, provenance, revisions and permissions. Federation envelopes can carry memories, albums, media, sources, relationships, source links and tombstones.

The federated historical explorer composes those envelopes into a place/time exploration. It preserves source-instance attribution, applies visibility controls, honours tombstones, deduplicates identical replicas and exposes divergent stable-ID content as conflict data.

### Interfaces
Web, API, search, maps, timelines and other interfaces consume protocol records. No interface should become the canonical owner of the underlying memory.

## Relationship model

The protocol should express relationships such as:

- person → appears_in → photograph
- person → remembers → event
- person → told → story
- story → variant_of → story
- story → translated_from → story
- memory → about → place
- manual → describes → process
- patent → protects → invention
- invention → predecessor_of → invention
- record → supported_by → evidence
- record → contradicts → record

## Historical exploration

A place/time query can combine:

- personal and collective memories
- oral and cultural stories
- historical/documentary evidence
- newspapers and archive sources
- Memory Albums
- photographs, audio and other media
- artefacts and technologies
- disagreements and contradictions
- timelines and graph connections

The distinction between these layers is preserved. An album remains an album; a newspaper remains a source; a remembered story remains a remembered story.

## Time

Time should not be reduced to one timestamp. A record may have creation time, remembered time, publication time, event time, approximate time, a time range or unknown time.

## Place

Location may range from exact coordinates to an address, named place, historical place name, region, country, approximate location or unknown. Privacy controls may deliberately reduce precision.

## Integrity

Content-derived identifiers and hashes may help detect corruption, duplication and transformation. They are integrity mechanisms, not replacements for human provenance.

## Implementation principle

Start with small, testable protocol contracts.

The first executable milestone should prove that a record can be:

1. created
2. validated
3. attributed
4. versioned
5. related to another record
6. exported without losing provenance


## Discovery and incremental synchronization

Federation discovery is decentralized. An instance can publish a machine-readable manifest describing public capabilities, record-type coverage, visibility classes and its current change cursor. No central registry is required by the protocol.

Incremental synchronization is cursor-based and transport-agnostic. A peer asks an instance for changes after its last successfully processed cursor. The response contains only the change envelopes in that window, plus a next cursor and a has_more signal. Tombstones are ordinary sync changes so withdrawals propagate without pretending the original record never existed.

The cursor is owned by the source instance. It is not a global clock and does not replace provenance timestamps.


## Reference node

The reference implementation includes a small dependency-free Python node using SQLite and the standard-library HTTP server. It exposes:

- `GET /health`
- `GET /federation/discovery`
- `GET /records`
- `POST /federation/publish`
- `POST /federation/sync`
- `POST /federation/import`

The node is deliberately replaceable. SQLite is local implementation storage, while protocol IDs, provenance, revisions, permissions and federation contracts remain portable.
