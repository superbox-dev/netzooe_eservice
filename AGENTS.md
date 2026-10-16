# AGENTS.md

Home Assistant custom integration (HACS) for the unofficial Netz Oberösterreich eService portal
(`eservice.netzooe.at`). All portal access goes through the separate PyPI library `netzooe_eservice_api`.

## Commands

The project uses `uv`. Always run tools through `uv run`.

```bash
./scripts/setup.sh                   # install dependencies + prek hooks
./scripts/develop.sh                 # start Home Assistant with ./config on http://127.0.0.1:8123
./scripts/lint.sh                    # ruff format, ruff check, ty, yamllint, rumdl
uv run pytest                        # tests (parallel, coverage, stops at first failure)
uv run pytest --snapshot-update      # regenerate syrupy snapshots in tests/snapshots/
```

Before you finish a change, run `./scripts/lint.sh` and `uv run pytest`.

## Rules

- **100% test coverage is enforced.** Every new code path needs a test.
- Python 3.14 and Home Assistant 2026.9.4 are the minimum. Don't use deprecated Home Assistant APIs.
- Line length 120, single-line imports, full type annotations including local variables.
- No new ignores in `ruff.toml` and no `# type: ignore`. `# noqa` only for the existing patterns
  (`ARG00x` for required signatures and lambdas, `TRY400`).
- Never touch `config/` except `config/configuration.yaml`. It is the local dev instance and may contain real
  credentials.
- Never use real credentials or customer data (contract account numbers, meter point numbers, ...) in code, tests
  or docs. Use the fake data in `tests/api_data.py`.
- Don't call the portal directly. Missing endpoints belong in `netzooe_eservice_api`.

## Architecture

Code lives in `custom_components/netzooe_eservice/`. The non-obvious parts:

- `coordinator.py`: `coordinator.data` maps a device identifier to the device's data dict. Its `deviceType`
  (`DeviceType`) decides which `SENSOR_*_TYPES` from `sensor.py` are created. With the "Frequent updates" option
  the coordinator runs every 15 minutes, but a full update runs only every 3 hours. In between only the
  contribution percentages and statuses of the energy communities are refreshed. On `APIError` the previous data
  is kept if it exists.
- `__init__.py` removes devices that are no longer in `coordinator.data` after every update.
- `strings.json` and `translations/en.json` must be **identical**. `translations/de.json` has the same keys.
  User-visible texts always use `translation_key`.

## Tests

HTTP is mocked with `FakeNetzOOEeServiceAPI` in `tests/conftest.py` and the responses in `tests/api_data.py`.
The `config_entry` fixture is parametrized indirectly with `data` / `options`. Patch
`custom_components.netzooe_eservice.coordinator.dt_util.now` for date-dependent values. After
`--snapshot-update`, review the diff in `tests/snapshots/*.ambr`.

## Changelog, versions and git

- Every user-visible change needs an entry under `## [Unreleased]` in `CHANGELOG.md` (Keep a Changelog).
  Entries start with an imperative verb ("Add ...", "Fix ..."). Issues are linked as `[(Issue #25)][issue-25]`.
- The version is in `pyproject.toml` and `manifest.json`. Only change it when asked. The `netzooe_eservice_api`
  requirement is in both files too. Run `uv lock` after changing it.
- Development happens on `develop`. `main` is the release branch. `v*` tags create a GitHub release for HACS.
- Only commit or push when asked. Don't edit `coverage-badge.svg`, CI updates it.
