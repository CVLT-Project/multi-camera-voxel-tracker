# ADR-VLT-014 — Admin access over SSH, separate from control of the loop

- **Status:** accepted · 2026-11-10 · decided by the sponsor (requirements review, gap G3) · amends ADR-VLT-003
- **Feature:** VLT

## Context

NF-VLT-10 required that no node accepts commands over the network, and its acceptance (no listening command port) also ruled out SSH. The team still has to install and update the nodes (NF-VLT-13), start and stop the software, change configuration and calibration files, and fetch logs, recordings and statistics (F-VLT-29, F-VLT-32, F-VLT-39). Nothing in the requirements said how.

## Decision

- **Admin access is allowed:** authenticated SSH (key only, no password login) from devices on the isolated demo network (NF-VLT-28). It covers installing and updating software, starting, stopping and restarting node software, reboot and shutdown, editing configuration and calibration files, and fetching logs, recordings and statistics.
- **Admin access never controls the running loop:** the loop processes have no command interface. Nothing over the network arms, disarms, starts a calibration or changes the running behaviour. Configuration and calibration changes take effect only when the node software restarts, and the restart then follows the existing rules (control or galvo restart → safe state, F-VLT-8/21; camera restart → F-VLT-17).
- **The monitoring software stays observe-only** (ADR-VLT-003): it receives data and sends nothing to the nodes. Admin access is a separate channel used by a person.

## Rationale

The team needs to administer five Pis without monitors or keyboards. The safety property that matters is that no network message can influence the loop's decisions. Forbidding all remote access doesn't add to that, and it would block development.

## Consequences

- NF-VLT-10 is rewritten; NF-VLT-28 allows a team machine for administration on the demo network.
- Restarting the control or galvo software over SSH while armed is a safety fault (safe state, re-arming per F-VLT-35), not a control path.

## Traces to

NF-VLT-10, NF-VLT-13, NF-VLT-28, F-VLT-8, F-VLT-17, F-VLT-21, F-VLT-29, F-VLT-32, F-VLT-35, F-VLT-39
