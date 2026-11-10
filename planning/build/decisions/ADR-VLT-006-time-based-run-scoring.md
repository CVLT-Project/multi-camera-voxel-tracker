# ADR-VLT-006 — Hit rate is scored by time; gaps count as misses

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-10)
- **Feature:** VLT

## Context

The purpose says "spot on the ball 80 % of the time", while F-VLT-7 counted fusion steps. Steps without a valid ball state could silently drop out of the count and inflate the hit rate.

## Decision

The hit rate of a run is the time with a hit divided by the run's duration. With the fixed-period fusion of ADR-VLT-009 every fusion slot weighs the same; a slot without a valid ball state, without a target or with the laser off counts as a miss. A run ended by the safe state is reported as *aborted* and counts as a failed run for NF-VLT-1. Release: the run starts when the ball, after being displaced more than 100 mm from rest, starts moving (speed above a configured threshold, default 100 mm/s) — so holding the ball out does not start the run.

## Rationale

Equals the sponsor's original criterion and makes gaps visible instead of removing them.

## Consequences

- F-VLT-7 and NF-VLT-1 are rewritten; the run result reports hit time, gap time and duration separately.
- The release speed threshold is [estimated] and confirmed on the reference data set.

## Traces to

F-VLT-7, NF-VLT-1, NF-VLT-21, NF-VLT-22
