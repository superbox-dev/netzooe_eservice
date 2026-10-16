# AGENTS.md

- Home Assistant custom integration (HACS)
- For the unofficial Netz Oberösterreich eService portal (`eservice.netzooe.at`)
- All portal access goes through the separate PyPI library `netzooe_eservice_api`

## Commands

- Use `uv`, always via `uv run`
- Setup: `./scripts/setup.sh` (dependencies + prek hooks)

```bash
uv run ruff format                   # format (lint.sh only checks)
./scripts/lint.sh                    # ruff, ty, yamllint, rumdl
uv run pytest                        # tests (parallel, coverage, stops at first failure)
uv run pytest --snapshot-update -n 0 # regenerate syrupy snapshots in tests/snapshots/ (serial!), then review the diff
./scripts/develop.sh                 # start Home Assistant with ./config on http://127.0.0.1:8123
```

Before finishing a change, run:

- `uv run ruff format`
- `./scripts/lint.sh`
- `uv run pytest`

## Rules

- **No breaking changes** for existing installations:
  - sensor `key`s (part of the `unique_id`)
  - device identifiers
  - option keys (`CONF_*`) and their default behaviour
  - `translation_key`s
- **Minimum versions**:
  - Python 3.14
  - Home Assistant 2026.9.4
  - no deprecated Home Assistant APIs
- Code style:
  - line length 120
  - single-line imports
  - full type annotations, including local variables
- No `# type: ignore`, no new `ruff.toml` ignores
- `# noqa` only for `ARG00x` in required signatures
- Every file starts with the copyright and SPDX header (`CPY001`)
- No real credentials or customer data:
  - applies to code, tests and docs
  - e.g. contract account numbers, meter point numbers
- Portal access:
  - never call the portal directly
  - missing endpoints belong in `netzooe_eservice_api`
- `git add` new files, CI only checks tracked files
- Never edit:
  - `config/`, except `config/configuration.yaml` (local dev instance, may contain real credentials)
  - `coverage-badge.svg` (updated by CI)

## Architecture

Code lives in `custom_components/netzooe_eservice/`.

- `coordinator.py`:
  - `coordinator.data` maps a device identifier to the device's data dict
  - `deviceType` (`DeviceType`) decides which `SENSOR_*_TYPES` from `sensor.py` are created
  - full update every 3 hours: dashboard, consents and contract accounts, then all consumption profiles
  - requests run in parallel, at most `MAX_PARALLEL_REQUESTS` at the same time
  - "Frequent updates" option (disabled by default):
    - coordinator runs every 15 minutes
    - in between full updates, only energy community contribution factors and statuses are refreshed
  - on `APIError` the previous data is kept, if it exists
  - on `AuthenticationError` the reauth flow starts
- `__init__.py`:
  - removes devices that are no longer in `coordinator.data` after every update
- `diagnostics.py`:
  - redacts credentials and customer numbers (`TO_REDACT`)
  - new customer data fields must be added to `TO_REDACT`
- `sensor.py`:
  - adds the sensors of new devices after every update, without reload
  - `unique_id` is `<device identifier>_<key>`
  - renaming a `key` creates new entities and orphans the old ones
  - energy community sensors come from `_energy_community_descriptions()`
  - the meter point totals reuse them via `_aggregated_descriptions()`
- Translations:
  - `strings.json` and `translations/en.json` must be **identical**
  - `translations/de.json` has the same keys
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
  - most values only change once a day, the portal is often briefly unavailable
  - do not change this
- Keep these rules satisfied:
  - `exception-translations`: exceptions use `translation_domain` and `translation_key`
  - `icon-translations`: icons in `icons.json`
  - `entity-device-class`: use a device class wherever one applies
    - `ENUM` needs `options` and state translations under `entity.sensor.<key>.state`
  - `entity-category`: `EntityCategory.DIAGNOSTIC` for diagnostic sensors
  - `entity-disabled-by-default`: rarely needed sensors get `entity_registry_enabled_default=False`
  - `dynamic-devices` / `stale-devices`: devices follow `coordinator.data` without reload
  - `diagnostics`: new customer data fields go into `TO_REDACT` in `diagnostics.py`
  - `log-when-unavailable`: log an outage once and log the recovery
  - `parallel-updates`: every platform sets `PARALLEL_UPDATES`
  - `reauthentication-flow` / `reconfiguration-flow`: keep both working
  - `test-coverage`: 100%, see [Tests](#tests)
- Documentation (`README.md`) covers:
  - installation parameters, options, removal
  - supported devices, sensors, data updates
  - use cases with an example, known limitations, troubleshooting
  - update it when sensors, options or behaviour change

## Adding a sensor

1. `sensor.py`: add a `NetzOOEeServiceSensorEntityDescription` to the matching `SENSOR_*_TYPES` list
2. `strings.json`, `translations/en.json`, `translations/de.json`: add the name under `entity.sensor.<key>`
3. `icons.json`: add the icon under `entity.sensor.<key>`, if it has no device class
4. `coordinator.py`: fetch the data, if it is not in `coordinator.data` yet
5. Tests: see [Tests](#tests)

## Adding an option

1. `const.py`: add `CONF_*` and `DEFAULT_*`
2. `config_flow.py`: add it to the options schema
3. `strings.json`, `translations/en.json`, `translations/de.json`: add `data` and `data_description`
4. `README.md`: add it to the options table

## Tests

- Run with `uv run pytest` (parallel, coverage, stops at first failure)
- **100% test coverage** is enforced, including branches:
  - every new code path needs a test
- Snapshots (syrupy) are in `tests/snapshots/`:
  - regenerate with `uv run pytest --snapshot-update -n 0`
  - parallel runs overwrite the snapshot files and drop snapshots
  - always review the diff, e.g. `tests/snapshots/test_sensor.ambr`
- New sensor:
  - add the API response to `tests/api_data.py`
  - regenerate the snapshots and review the new entities
- HTTP is mocked with `FakeNetzOOEeServiceAPI` in `tests/conftest.py` and the responses in `tests/api_data.py`
- Only use the fake data in `tests/api_data.py`, never real customer data
- The `config_entry` fixture is parametrized indirectly with `data` / `options`
- Patch `custom_components.netzooe_eservice.coordinator.dt_util.now` for date-dependent values
- Never test or patch internal methods or attributes (e.g. `coordinator._async_update_data()`):
  - set up the integration and drive it via the mocked HTTP responses
  - trigger updates with `coordinator.async_refresh()`
  - assert entity states, `ConfigEntryState` or the requested URLs

## Changelog, versions and git

- `CHANGELOG.md`:
  - every user-visible change gets an entry under `## [Unreleased]`
  - Keep a Changelog format, past tense
  - identifiers in backticks
  - issues as `([Issue #25][issue-25])`
  - releases are linked at the bottom:
    - `[Unreleased]` compares the latest tag with `HEAD`
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
