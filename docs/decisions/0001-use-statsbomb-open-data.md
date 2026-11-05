# 0001 — Use StatsBomb open data

- **Date:** 2026-11-05
- **Status:** Accepted

## Context

I need free, event-level football data that I am allowed to use and publish results from.

## Options considered

1. StatsBomb Open Data — free, well documented, event-level with xG, Python library available.
2. Scraping stats websites — often forbidden by their terms, and fragile.
3. Paid data APIs — not affordable for a student project.

## Decision

Use StatsBomb Open Data via `statsbombpy`, with attribution.

## Consequences

- Limited to the competitions StatsBomb has released.
- Must credit StatsBomb in the README and any public posts.
