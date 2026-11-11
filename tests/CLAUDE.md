# Tests

- Every new code path needs a test
- Mock HTTP with the `fake_api` fixture (`tests/conftest.py`)
  - responses of a complete account in `tests/fixtures/account/`, one JSON file per response at the path of the
    request URL, exactly as the portal returns it
  - loaded by the `portal_account` fixture, another account in `tests/fixtures/` as its indirect parameter
- Assert entities with snapshots in `tests/snapshots/`
- New entity:
  - add the values to the responses in `tests/fixtures/account/`
  - regenerate the snapshots and review the new entities
- Time frozen at `NOW` (`tests/const.py`) by the autouse `frozen_time` fixture, another time as its indirect
  parameter
- Test only through Home Assistant:
  - exception: static checks of files (e.g. `test_translations.py`), with `_`-prefixed helpers in the test module
  - never call, patch or inspect `_`-prefixed methods or attributes of the integration
  - never patch the API library, mock its HTTP requests instead
  - only patch: `async_setup_entry` with `mock_setup_entry` in config, reauth and reconfigure flow tests
  - set up the integration with `init_integration`, or `setup_integration()` after changed responses
  - drive it through the mocked HTTP responses
  - trigger updates with `next_update()` (`freezer`, `async_fire_time_changed()`), never through `runtime_data`
  - assert entity states, `ConfigEntryState`, the device registry or the requested URLs
- `pytest.mark.parametrize` with `ids=` naming each case
- Constants of a test module in a module with its name and `_data.py` (`test_api.py` → `test_api_data.py`)
  - shared by several test modules: `tests/const.py`
- Helper functions that only check (no return value) start with `assert_`
  - helpers that return a value and only assert to narrow types keep their name
  - shared by several test modules: `tests/asserts.py`, registered with `pytest.register_assert_rewrite()` in
    `tests/conftest.py`
- Tests as functions, no test classes
- Error cases next to the tests of the code they check, named `test_<function>_<condition>`
- Every bug fix gets a regression test that fails without the fix
- Exceptions: assert the type and the message (`pytest.raises(..., match=...)` or `error.value`)
- Never wait in real time, advance the time with `freezer`, no `sleep()`
- Fixtures only in `tests/conftest.py`
- Tests are independent of each other, they run in parallel (`pytest-xdist`) and in any order
- No logic in tests (`if`, loops over cases), use `parametrize` instead
  - except loops that only build test data
