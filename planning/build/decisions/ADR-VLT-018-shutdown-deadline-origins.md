# ADR-VLT-018 — Explicit shutdown origins and qualification intervals

- **Status:** decided · 2026-11-10 · user requested resolution of the 100 ms / 600 ms ambiguity; measured verification remains pending.
- **Feature:** VLT
- **Amends:** ADR-VLT-008/010/015, NF-VLT-23/26/29/30/34

## Context

The general unsafe-condition transaction used 100 ms, while effect monitoring deliberately waits 500 ms and then shuts down within 100 ms, and the on-chip watchdog has a 1 s bound. A blanket 600 ms converter link-fault claim also assumed that every electrical fault necessarily produces a qualifying optical effect.

## Decision

| Transaction | Origin | Bound and scope |
| --- | --- | --- |
| T2 — missing target | Last fresh valid target at the galvo node, local monotonic time | ≤ 100 ms + 10 ms to physical off (F-VLT-10) |
| T3 — fast unsafe-condition response | First valid exposure showing an immediately qualifying image condition; otherwise the relevant local event/expiry | ≤ 100 ms to off; no 500 ms persistence interval. F-VLT-25's explicit status-loss allowance remains ≤ 110 ms. |
| T6 — persistent large aiming error | First valid exposure with error > 50 mm beginning the qualifying episode | 500 ms qualification + ≤ 100 ms off, ≤ 600 ms total; a fresh error ≤ 50 mm clears the episode |
| T6 — unavailable measurable optical effect | First laser-on placement, or last accepted current measurable effect update; timer progresses monotonically | 500 ms watchdog + ≤ 100 ms off, ≤ 600 ms total; mode-specific outcome in ADR-VLT-019 |
| T7 — galvo output-loop hang | Actual output-loop hang | ≤ 1 s total to physical off, including watchdog reset and laser-disable delay; no extra boot-time allowance |

T1 remains firm (exposure → placement p99 ≤ 30 ms); T4 is soft monitoring and T5 reintegration has no deadline. The 100 ms response after a T6 condition qualifies does not replace its 500 ms qualification timer. A spot > 20 mm outside the cube is T3 immediately, not a 500 ms-confirmed error. Local output-stop detection also uses T3; a stopped/hung output loop unable to execute that detector instead uses T7. Other faster applicable rules, including ball loss and kill switch, always win.

Clock/sync-status and observation age expiry remain governed by their camera-dependent freshness limits in OQ-12. No new numeric camera detection delay, exposure timing, frame rate or update period is selected here. For each timed fault use its specified origin; recording only from the later alarm is insufficient for T6 acceptance.

**Converter coverage:** there is no electrical read-back. A fault producing an outside-cube spot, persistent large error or unavailable measurable effect is covered by that effect's T3/T6 rule. A fault producing no qualifying observable effect has no promised electrical detection time. Record electrical fault injection separately from first qualifying optical evidence/watchdog origin; do not label an unobservable fault a successful “detected within 600 ms” case. The independent kill switch and existing residual-risk entries remain.

## Rationale

Separating qualification, response and watchdog fallback gives each existing limit a clear scope. It avoids strengthening the accepted effect-monitoring hardware decision into a detection guarantee that the chosen interface cannot establish.

## Acceptance

Independent instruments verify T2/T3/T6/T7 against their stated origins. At least 100 samples each remain required for T1/T2/T3; at least ten injections per applicable T6/T7 matrix case are recorded. Test immediate outside-cube shutdown, both T6 branches, faster-fault precedence and total hang-to-off time. Include a converter fault without a qualifying effect and report the coverage limitation. Bounds are measured targets under the fault hypothesis, not a proof from the non-real-time OS.

## Traces to

F-VLT-10/15/16/21/25/26/42, NF-VLT-23/26/29/30/34, ADR-VLT-008/010/015/019
