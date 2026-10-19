# CLAUDE.md

Home Assistant custom integration (HACS) for the unofficial Netz Oberösterreich eService portal
(`eservice.netzooe.at`), with all portal access going through the separate PyPI library `netzooe_eservice_api`.

## Commands

- Use `uv`, always via `uv run`
- Setup: `./scripts/setup.sh`

```bash
uv run ruff format                   # format (lint.sh only checks)
./scripts/lint.sh                    # all linters and type checks
uv run pytest                        # tests + coverage
uv run pytest --snapshot-update -n 0 # regenerate snapshots (serial only), then review the diff
./scripts/develop.sh                 # start a local Home Assistant instance with ./config
./scripts/docs.sh                    # docs (Docusaurus, needs Node.js)
./scripts/docs.sh start              # docs with live reload
```

Before finishing a change, run all of them except the snapshot update, `develop.sh` and the live reload.

## Rules

- **No breaking changes** for installations: never change what Home Assistant stores or users reference
  (IDs, keys, option defaults)
- No deprecated Home Assistant APIs
- Type annotations also for local variables
- Every `.py` file starts with (after the shebang of an executable script):

  ```python
  # Copyright 2026 Michael Hacker
  # SPDX-License-Identifier: Apache-2.0
  ```

- No new lint/type suppressions or `# pragma: no cover`, fix or test the code
  - only exception: `# noqa: ARG00x` in required signatures
- No real credentials or customer data, use the fake data in `tests/api_data.py`
- Missing portal endpoints or values belong in `netzooe_eservice_api`
- `strings.json` and `translations/en.json` identical, `translations/de.json` with the same keys
- Never edit generated files (`coverage-badge.svg`) or `config/` (except `config/configuration.yaml`)
- **Never edit `CLAUDE.md` files or `.claude/skills/` on your own**, only when asked
  - if a change conflicts with them, stop and ask

## Architecture

- Follow the Home Assistant integration conventions, code in `custom_components/netzooe_eservice/`

## Quality scale

- Goal: every applicable rule of the [integration quality scale](https://contributors.home-assistant.io/core/quality-scale/),
  audit with the `quality-scale` skill
- Intended deviations, **never change them**:
  - `entity-unavailable`: on `APIError` entities keep their last values and stay available (portal often briefly
    down, values change rarely)
  - own `entity_id` `<platform>.netzooe_eservice_<unique_id>` on every platform (stable IDs in automations)
- `entity-device-class`: use a device class wherever one applies
  - `ENUM` needs `options` and state translations under `entity.<platform>.<key>.state`
- `entity-category`: `EntityCategory.DIAGNOSTIC` for diagnostic entities
- `entity-disabled-by-default`: rarely needed entities get `entity_registry_enabled_default=False`
- `diagnostics`: new customer data fields go into `TO_REDACT`
- `log-when-unavailable`: log an outage once and log the recovery
- `parallel-updates`: every platform sets `PARALLEL_UPDATES`
- The coordinator gets `config_entry` explicitly
- Large or growing attributes go into `_unrecorded_attributes`
- Repeated warnings are logged once until the cause is gone
- The options flow works without a loaded config entry

## Documentation

- Update `website/content/index.md` when entities, options or behaviour change
- Keep the `<!--start-…-->` / `<!--end-…-->` markers in `README.md`, `CONTRIBUTING.md` and `CHANGELOG.md`
- Keep `README.md` short (install, links to the sections), details go to `website/content/index.md`
- Images are in `assets/` (also used by `README.md`)

## Changelog, versions and git

- Every user-visible change gets an entry under `## [Unreleased]` in `CHANGELOG.md`, use the `changelog` skill
- Version: only change it when asked, use the `release` skill
- `netzooe_eservice_api` requirement is in `pyproject.toml` and `manifest.json`, run `uv lock` after changing it
- Work on `develop`
- Only commit or push when asked
