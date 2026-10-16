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
uv run pytest --snapshot-update      # regenerate syrupy snapshots in tests/snapshots/, then review the diff
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
- **100% test coverage** is enforced:
  - every new code path needs a test
- **Minimum versions**:
  - Python 3.14
  - Home Assistant 2026.9.4
  - no deprecated Home Assistant APIs
- Code style:
  - line length 120
  - single-line imports
  - full type annotations, including local variables
- No `# type: ignore`, no new `ruff.toml` ignores
- `# noqa` only for the existing patterns:
  - `ARG00x` for required signatures and lambdas
  - `TRY400`
- No real credentials or customer data:
  - applies to code, tests and docs
  - e.g. contract account numbers, meter point numbers
  - use the fake data in `tests/api_data.py`
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
  - full update every 3 hours
  - "Frequent updates" option (disabled by default):
    - coordinator runs every 15 minutes
    - in between full updates, only energy community contribution factors and statuses are refreshed
  - on `APIError` the previous data is kept, if it exists
- `__init__.py`:
  - removes devices that are no longer in `coordinator.data` after every update
- `sensor.py`:
  - `unique_id` is `<device identifier>_<key>`
  - renaming a `key` creates new entities and orphans the old ones
- Translations:
  - `strings.json` and `translations/en.json` must be **identical**
  - `translations/de.json` has the same keys
  - user-visible texts always use `translation_key`

## Adding a sensor

1. `sensor.py`: add a `NetzOOEeServiceSensorEntityDescription` to the matching `SENSOR_*_TYPES` list
2. `strings.json`, `translations/en.json`, `translations/de.json`: add the name under `entity.sensor.<key>`
3. `coordinator.py`: fetch the data, if it is not in `coordinator.data` yet
4. Tests:
   - add the API response to `tests/api_data.py`
   - run `uv run pytest --snapshot-update`
   - review the diff in `tests/snapshots/test_sensor.ambr`

## Adding an option

1. `const.py`: add `CONF_*` and `DEFAULT_*`
2. `config_flow.py`: add it to the options schema
3. `strings.json`, `translations/en.json`, `translations/de.json`: add `data` and `data_description`
4. `README.md`: add it to the options table

## Tests

- HTTP is mocked with `FakeNetzOOEeServiceAPI` in `tests/conftest.py` and the responses in `tests/api_data.py`
- The `config_entry` fixture is parametrized indirectly with `data` / `options`
- Patch `custom_components.netzooe_eservice.coordinator.dt_util.now` for date-dependent values

## Changelog, versions and git

- `CHANGELOG.md`:
  - every user-visible change gets an entry under `## [Unreleased]`
  - Keep a Changelog format, entries start with an imperative verb ("Add ...", "Fix ...")
  - identifiers in backticks
  - issues as `[(Issue #25)][issue-25]`
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
