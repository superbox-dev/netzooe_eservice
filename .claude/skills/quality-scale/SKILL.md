---
name: quality-scale
description: Status and audit of the Home Assistant integration quality scale. Use when checking, auditing or improving quality scale rules.
---

# Quality scale

- Audit: check every rule against the code, including the rules under `## Quality scale` in `CLAUDE.md`
- All applicable rules are done
- Not applicable:
  - `action-setup`, `action-exceptions`, `docs-actions`: no actions
  - `docs-conditions`, `docs-triggers`: no conditions or triggers
  - `entity-event-setup`: entities only use the coordinator
  - `discovery`, `discovery-update-info`: cloud service
  - `repair-issues`: a changed password is handled by the reauth flow
- Keep satisfied:
  - `dynamic-devices` / `stale-devices`: devices follow `coordinator.data` without reload
  - `reauthentication-flow` / `reconfiguration-flow`: keep both working
    - `reauth_confirm` only asks for the password, `reconfigure` for username and password
