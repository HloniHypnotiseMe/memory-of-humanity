# The Memory of Humanity

**A protocol for humanity to remember itself.**

The Memory of Humanity is an open-source protocol and reference implementation for preserving human memories, stories, cultural knowledge, evidence, places, people, media, and the practical knowledge of how things were made.

It is designed as federatable memory infrastructure: families, communities, archives, museums, researchers, and individuals can operate their own instances while preserving interoperable records and provenance.

## Core idea

Humanity does not only forget events. It forgets what people experienced, what families remember, the stories people told, what communities practiced, what places used to look and sound like, and how things were made and repaired.

This project preserves those layers without pretending they are all the same kind of truth.

## Principles

1. Memory is not automatically fact.
2. AI is not an authority.
3. Disagreement is data.
4. Revision does not require deletion.
5. Provenance travels with knowledge.
6. Context matters.
7. Contributors retain agency over their contributions.
8. Uncertainty is legitimate.
9. Communities can govern their own material.
10. Original contributions remain distinguishable from interpretation.

## What belongs here?

- family photographs and albums
- personal memories and oral histories
- folklore, myths, legends and story variants
- community memories
- historical and documentary records
- maps and place memories
- languages and cultural practices
- recipes, crafts and traditional techniques
- repair and manufacturing knowledge
- old technical books and manuals
- engineering drawings and formulas
- patents and technological lineages
- knowledge from retired tradespeople
- AI-assisted transcription, translation and discovery, clearly marked as derived material

## Technology archaeology

A central part of the project is preserving practical knowledge that disappears when technologies become obsolete.

Patent expiration can be relevant to this research, but an expired patent does not automatically mean every related work is free of all legal restrictions. Patent, copyright, trade-secret, trademark, safety and jurisdictional considerations must remain separately represented.

## Status

This repository starts as a protocol/reference implementation project. The architecture will be built from the data model outward:

**records → provenance → relationships → revisions → federation → interfaces**

Federation now includes decentralized instance discovery, cursor-based incremental synchronization, deterministic import reconciliation, tombstone propagation, stable-ID conflict detection, and auditable source-instance attribution.

AI is an optional interpretation and indexing layer, not a prerequisite for preserving the underlying record.

## License

The project's open-source license and governance model will be selected explicitly as the protocol stabilizes.


## Runnable reference node

The repository now includes a dependency-free Python reference node under `node/`. It uses SQLite for local storage and exposes discovery, incremental sync, import reconciliation and publishing endpoints over a small HTTP server.

Run:

    python -m node.cli --port 8787

The node is an implementation of the protocol, not the protocol itself. Storage can be replaced, and other implementations can interoperate through the protocol contracts.

## Runnable memory node

The reference implementation now includes a small local application on top of the protocol. It persists contributor identities and consent records locally, captures memories, creates Memory Albums, searches original records, exposes place-history exploration, and exposes federation discovery/sync endpoints.

Run it with:

    python -m node.cli --port 8787

Open http://127.0.0.1:8787/ in a browser.

### Local application API

- `POST /api/identities` — create a local contributor identity
- `POST /api/consents` — record consent scope/status
- `POST /api/memories` — preserve a memory as a protocol record
- `GET /api/search?q=...` — deterministic search over original records
- `GET /api/albums` / `POST /api/albums` — Memory Albums
- `GET /api/place-history?place_id=moh:place:...` — time-layered place exploration
- `GET /api/discovery` — instance discovery metadata

The local identity is a reference-node identity, not a production authentication system. A deployment that serves real communities must add appropriate authentication, authorization, consent UX, privacy controls, secure media storage, and governance.
