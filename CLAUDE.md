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

Before finishing a change, run `ruff format`, `lint.sh` and `pytest`, in this order.
`docs.sh` only when `website/`, `README.md`, `CONTRIBUTING.md` or `CHANGELOG.md` changed.

## Rules

- **No breaking changes** for installations: nothing a user notices later and has to fix by hand
  (unique IDs, entity `key`s, entity IDs, device identifiers, config entry data, option keys and defaults, removed
  entities, device classes, units, state classes, enum states)
  - only when asked, then as a major release
- No deprecated Home Assistant APIs
- Type annotations also for local variables (not for loop, `with`, `except`, comprehension or unpacking targets)
  - union order, also in `isinstance()`: general before specific types, each alphabetical, containers after
    single types and less nested first, `None` last (`float | int | str`, `Exception | HTTPStatus`,
    `Value | list[Value] | list[list[Value]] | None`)
  - type alias for complex annotations (nested or repeated unions)
- Module-level constants with `Final` (`NAME: Final = ...`)
- Comments as complete sentences with a trailing period
- `TypedDict` only for JSON data from or to the portal (optional keys as `NotRequired`), `NamedTuple` only for
  small values that are unpacked (points, pairs), otherwise `@dataclass(frozen=True, kw_only=True)`, mutable only
  when needed
- `Enum` for a fixed set of values (modes, states, types, values of the portal), never loose strings or ints
  for them
  - not for open values (names, IDs, numbers) or a one-off choice in a signature (`Literal`)
- Parameters: options keyword-only (after `*`), `/` only for `_`-prefixed helpers
- Credentials, tokens and serial numbers never in log or exception messages, dumps of device or portal data only
  redacted (`async_redact_data(data, TO_REDACT)`)
- New texts in `strings.json`, `translations/en.json` and `translations/de.json`, keys sorted
- Log messages start with a capital letter, no trailing period, values as `%s` arguments
- Every file follows `.editorconfig`, whether a linter checks it or not
- Style rules apply to new and changed code, existing code only adapted when asked
- Every `.py` file starts with (after the shebang of an executable script, update the end year when editing a
  file, a single year while it equals the start year):

  ```python
  # Copyright 2026-<current year> Michael Hacker
  # SPDX-License-Identifier: Apache-2.0
  ```

- No inline lint/type suppressions, no new ones in the config, no `# pragma: no cover`, fix or test the code
  - only exception: `# noqa: ARG00x` in required signatures
- No real credentials or customer data, use the fake data in `tests/api_data.py`
- Missing portal endpoints or values belong in `netzooe_eservice_api`, stop and ask how to proceed
  - values calculated from existing ones are fine in the integration
- No new dependencies (`pyproject.toml`, `manifest.json`, also dev dependencies) without asking first
- `git add` new files, the pre-commit hooks only check tracked files
- Never edit generated files (`coverage-badge.svg`) or `config/` (except `config/configuration.yaml`)
- **Never edit `CLAUDE.md` files or `.claude/skills/` on your own**, only when asked
  - if a change conflicts with them, stop and ask

## Architecture

- Follow the Home Assistant integration conventions, code in `custom_components/netzooe_eservice/`
- Helpers are `_`-prefixed methods of the class that uses them (`@staticmethod` if they need no `self`)
  - module-level functions only when shared across classes or modules, for Home Assistant callbacks (action
    handlers, validators), as helpers of module-level Home Assistant functions (`async_setup_entry`) or to build
    the entity descriptions of a platform
- Constants always in `const.py`
  - except what Home Assistant reads from the module itself (`_LOGGER`, `PARALLEL_UPDATES`, `CONFIG_SCHEMA`) and
    the entity descriptions of a platform (`SENSOR_TYPES`, ...)
- Class member order: `__init__`, dunder methods, properties, public methods (also Home Assistant overrides)
  grouped by topic, helpers directly below their first caller
  - applies to new methods, existing ones only moved when asked

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
- `entity-disabled-by-default`: `entity_registry_enabled_default=False` for redundant or derived entities, entities
  only for diagnosis or service, or entities only useful for rare setups
- `diagnostics`: new customer data fields go into `TO_REDACT`
- `log-when-unavailable`: log an outage once and log the recovery
- `parallel-updates`: every platform sets `PARALLEL_UPDATES`
- The coordinator gets `config_entry` explicitly
- Large or growing attributes go into `_unrecorded_attributes`
- Repeated warnings are logged once until the cause is gone
- The options flow works without a loaded config entry, its options need no runtime data

## Documentation

- Update `website/content/index.md` when entities, options or behaviour change
- Keep the `<!--start-…-->` / `<!--end-…-->` markers in `README.md`, `CONTRIBUTING.md` and `CHANGELOG.md`
- Keep `README.md` short (install, links to the sections), details go to `website/content/index.md`
- Images are in `assets/` (also used by `README.md`)

## Changelog, versions and git

- Every change users notice gets an entry under `## [Unreleased]` in `CHANGELOG.md` (not refactorings, tests, CI,
  `CLAUDE.md` or skills), use the `changelog` skill
- Version: only change it when asked, use the `release` skill
- `netzooe_eservice_api` requirement is in `pyproject.toml` and `manifest.json`, run `uv lock` after changing it
- Work on `develop`
- Only commit or push when asked
- Commit message of a change for an issue starts with its number (`#67 Fix sensors that are not in use`)
