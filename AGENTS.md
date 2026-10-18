# AGENTS.md

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

- **No breaking changes** for existing installations:
  - entity description `key`s (part of the `unique_id`)
  - device identifiers
  - option keys (`CONF_*`) and their default behaviour
  - `translation_key`s
- **Minimum versions**:
  - Python as in `pyproject.toml`, Home Assistant as in `hacs.json`
  - no deprecated Home Assistant APIs
- Code style:
  - line length 120
  - single-line imports
  - full type annotations, including local variables
- Every `.py` file starts with (after the shebang of an executable script):

  ```python
  # Copyright 2026 Michael Hacker
  # SPDX-License-Identifier: Apache-2.0
  ```

- NumPy-style docstrings everywhere, also in tests
- No lint or type suppressions (inline or in config), except the existing ignores in `ruff.toml`. Fix the code instead
  - only inline exception: `# noqa` for `ARG00x` in required signatures
- Avoid `cast()`: narrow types with checks that also run at runtime (e.g. `isinstance`) or with generics
- No real credentials or customer data, use placeholders like `"test"`
- Portal access:
  - never call the portal directly
  - missing endpoints belong in `netzooe_eservice_api`
- `git add` new files, CI only checks tracked files
- Never edit generated or CI-managed files (`coverage-badge.svg`)
- Never edit `config/`, except `config/configuration.yaml` (local dev instance, may contain real credentials)

## Architecture

Code lives in `custom_components/netzooe_eservice/`.

- `coordinator.py`:
  - `coordinator.data` maps a device identifier to the device's data
  - the device type decides which entity descriptions from `sensor.py` are used
  - full updates run in a fixed interval, requests run in parallel up to a limit
  - an option enables more frequent, partial updates in between
  - on `APIError` the previous data is kept, if it exists
  - on `AuthenticationError` the reauth flow starts
- `__init__.py`:
  - removes devices that are no longer in `coordinator.data` after every update
- `diagnostics.py`:
  - redacts credentials and customer data (`TO_REDACT`)
- `sensor.py`:
  - adds the entities of new devices after every update, without reload
  - `unique_id` is `<device identifier>_<key>`
  - renaming a `key` creates new entities and orphans the old ones
- Translations:
  - `strings.json` and `translations/en.json` must be **identical**
  - all other translations have the same keys
  - user-visible texts always use `translation_key`
  - exceptions use `translation_domain` and `translation_key` (`exceptions` in `strings.json`)
  - icons are in `icons.json`, never `icon=` in descriptions

## Quality scale

- Goal: every applicable rule of the [integration quality scale](https://contributors.home-assistant.io/core/quality-scale/)
- All applicable rules are done
- Not applicable:
  - `action-setup`, `action-exceptions`, `docs-actions`: no actions
  - `docs-conditions`, `docs-triggers`: no conditions or triggers
  - `entity-event-setup`: entities only use the coordinator
  - `discovery`, `discovery-update-info`: cloud service
  - `repair-issues`: a changed password is handled by the reauth flow
- Intended deviation, `entity-unavailable`:
  - on `APIError` the entities keep their last values and stay available
  - the values change rarely, the portal is often briefly unavailable
  - do not change this
- Intended deviation, own `entity_id`:
  - `sensor.py` sets `entity_id` to `sensor.netzooe_eservice_<unique_id>`
  - Home Assistant only treats it as a suggestion, the entity registry wins
  - keeps the IDs stable, e.g. when a removed device comes back
  - do not change this, it breaks the entity IDs in automations
- Keep these rules satisfied:
  - `exception-translations`: exceptions use `translation_domain` and `translation_key`
  - `icon-translations`: icons in `icons.json`
  - `entity-device-class`: use a device class wherever one applies
    - `ENUM` needs `options` and state translations under `entity.<platform>.<key>.state`
  - `entity-category`: `EntityCategory.DIAGNOSTIC` for diagnostic entities
  - `entity-disabled-by-default`: rarely needed entities get `entity_registry_enabled_default=False`
  - `dynamic-devices` / `stale-devices`: devices follow `coordinator.data` without reload
  - `diagnostics`: new customer data fields go into `TO_REDACT`
  - `log-when-unavailable`: log an outage once and log the recovery
  - `parallel-updates`: every platform sets `PARALLEL_UPDATES`
  - `reauthentication-flow` / `reconfiguration-flow`: keep both working
    - `reauth_confirm` only asks for the password, `reconfigure` for username and password
  - `test-coverage`: 100%, see [Tests](#tests)
- Also keep:
  - the coordinator gets `config_entry` explicitly
  - large or growing attributes go into `_unrecorded_attributes`
  - repeated warnings are logged once until the cause is gone
  - the options flow works without a loaded config entry
- Documentation (`website/content/index.md`, see [Documentation](#documentation)) covers:
  - installation parameters, options, removal
  - supported devices, entities, data updates
  - use cases, examples, known limitations, troubleshooting
  - update it when entities, options or behaviour change

## Adding a sensor

1. `sensor.py`: add an entity description to the matching list
2. `strings.json` and all translations: add the name under `entity.sensor.<key>`
3. `icons.json`: add the icon under `entity.sensor.<key>`, if it has no device class
4. `coordinator.py`: fetch the data, if it is not in `coordinator.data` yet
5. Tests: see [Tests](#tests)

## Adding an option

1. `const.py`: add `CONF_*` and `DEFAULT_*`
2. `config_flow.py`: add it to the options schema
3. `strings.json` and all translations: add `data` and `data_description`
4. `website/content/index.md`: add it to the options table

## Documentation

- Docusaurus website in `website/`, deployed to GitHub Pages from `main` (`.github/workflows/page.yml`)
- `scripts/generate-docs.py` writes all pages into `website/docs/` (not tracked, run by `scripts/docs.sh`):
  - hand-written pages from `website/content/`
  - donation, contributing and changelog from the `<!--start-…-->` / `<!--end-…-->` markers
    in `README.md`, `CONTRIBUTING.md` and `CHANGELOG.md`, so keep the markers
- `website/content/index.md` is the integration page:
  - sections in the order of the home-assistant.io integration pages
  - examples use placeholder entity IDs, no real meter point numbers
- Keep `README.md` short (install, links to the sections), details go to `website/content/index.md`
- Design after home-assistant.io:
  - `website/src/css/custom.css` and the wrapped `website/src/theme/TOC/`
  - the integration card in `website/src/components/ProjectInfo/` reads `manifest.json` and `hacs.json`
  - the brand images in `custom_components/netzooe_eservice/brand/` are served from the website root

## Tests

- **100% test coverage** (lines and branches) is enforced
  - every new code path needs a test
- Mock HTTP with the fake API client in `tests/conftest.py` and the responses in `tests/api_data.py`
- Assert the entities with snapshots in `tests/snapshots/`:
  - regenerate them serially (`-n 0`), parallel runs drop snapshots
  - always review the diff
- New sensor:
  - add the API response to `tests/api_data.py`
  - regenerate the snapshots and review the new entities
- The `config_entry` fixture is parametrized indirectly with `data` / `options`
- Patch `dt_util.now` in the module under test for date-dependent values
- Test only through Home Assistant:
  - never call, patch or inspect `_`-prefixed methods or attributes
  - set up the integration and drive it through the mocked HTTP responses
  - trigger updates with `coordinator.async_refresh()`
  - assert entity states, `ConfigEntryState` or the requested URLs

## Changelog, versions and git

- `CHANGELOG.md`:
  - every user-visible change gets an entry under `## [Unreleased]`
  - Keep a Changelog format, past tense
  - identifiers in backticks
  - issues as `([Issue #25][issue-25])`, pull requests as `([PR #19][pr-19])`
  - issue and PR links are defined at the end of their release section, not at the bottom
  - releases are linked at the bottom, before `<!--end-->`:
    - `[Unreleased]` compares the latest release tag (no pre-release) with `HEAD`
    - each release compares its tag with the previous one
    - the first release links to its release tag
- Versions:
  - the version is in `pyproject.toml` and `manifest.json`
  - only change it when asked
  - the `netzooe_eservice_api` requirement is in both files too
  - run `uv lock` after changing it
- Branches:
  - work on `develop`
  - `main` is the release branch
  - `v*` tags create a GitHub release for HACS
- Only commit or push when asked
