# Lecture sources for the DRS reports

[L] = "Distributed Real-Time Systems", lecture slides WS26, 308 pages (`drs-fhha-ws26-slides.pdf`, outside the repository). Page = PDF page number. Use these pages as the lecture source of every requirement that contains a time (report rule M3).

Note: the M2 report cited a 12-page exercise slide set as [L]; its page numbers do not apply to this deck.

## DRS requirements checklist of the lecture (p. 287–288)

Rule (p. 287): "Where an item is given to us — an existing bus, a fixed sensor — it is a requirement. Where we choose it, it belongs in the architecture document."

1. desired end-to-end functions at system level
2. modes of operation and possible configurations
3. structure of all components — nodes, networks, gateways, I/O
4. interfaces — structure, timing, control mechanisms
5. messages and data elements — semantics, coding, size
6. timing of actions — WCET, minimum and maximum period
7. end-to-end deadline of each transaction, and its budget per stage
8. temporal accuracy — how old each value may be when it is used
9. time base — the required precision of the global time
10. startup, restart and mode changes
11. resource requirements — memory, CPU, I/O
12. fault-tolerance requirements — the fault hypothesis
13. performance requirements — the load hypothesis
14. failure modes of the nodes
15. error detection coverage — numbers and mechanisms
16. safety requirements
17. security requirements
18. traceability — every item points to its check

Architecture document contents: p. 290. Project standards (units, naming, versioning): p. 289. V-model phases, gate before architecture: p. 20.

## Page index by topic

| Topic | Pages |
| --- | --- |
| V-model in the exercise, review gate before architecture | 10–20 (gate: 20) |
| Transaction, example budget, where the numbers come from | 36–40, 48–49, 76–78, 292–299 |
| Deadline; soft / firm / hard | 52–53 |
| Resource adequacy, trigger of action (event / time) | 55–56, 83–85, 185 |
| Load and fault hypothesis | 60 |
| Temporal obligations: d_RESP, d_WCET, d_MINT | 65 |
| Duration of actions, statistics, WCET | 67–68, 72–75 |
| H-state and ground state | 79 |
| Global time, offset, precision π, accuracy | 80–82, 89–96 (π: 92) |
| Reasonableness condition g > π | 97 |
| Limits of time measurement, ±2g | 98 |
| Clock synchronization, condition, central sync, jitter, correction | 99–106 |
| RT entity, RT image, observation | 108–113 |
| Update delay | 114 |
| Temporal accuracy d_acc | 116–119 |
| Phase-sensitive RT images: d_update + period + WCET < d_acc | 120–121 |
| Composability | 128 |
| State and event messages | 130 |
| Flow control, PAR, implicit flow control | 131–134 |
| Communication error handling, thrashing, gateway | 137–140 |
| Permanence, action delay (+2g with global timestamps) | 146–148 |
| Non-blocking write, error detection, message / control-flow monitoring | 161–164 |
| Watchdog (heartbeat at the end of the output task) | 167 |
| Scheduling, priority inversion, COTS, static / time-triggered | 171–185 |
| Mode changes (take effect at the ground state) | 186 |
| Sampling, state vs. event, lost message | 195–200 |
| End-to-end protocol (monitor the effect, not the command) | 206–207 |
| Dependability: reliability, availability, safety, security | 211–218 |
| Failures, errors, faults | 220–225 |
| Node as unit of failure, TMR, voters, fail-silent | 229–234 |
| Single point of failure, idempotent messages | 235–237 |
| Reintegration | 240 |
| Membership service, cliques, degraded mode | 243 |
| Fault-tolerant actuators | 247–248 |
| Error handling strategy, reaction matrix (error → detection → reaction → time limit → log) | 249–256 (matrix: 254) |
| Test levels, traceability, testing the temporal domain | 258–266 (temporal: 266) |
| Design for testability, test doubles, system test | 267–272 |
| Validation, functional safety | 273–276 |
| Integration testing, cluster simulation, probe effect | 279–282 |
| Test selection, fault injection | 283–284 |
