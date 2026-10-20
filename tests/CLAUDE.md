# Tests

- Every new code path needs a test
- Mock HTTP with the `fake_api` fixture (`tests/conftest.py`), responses in `tests/api_data.py`
- Assert entities with snapshots in `tests/snapshots/`
- New entity:
  - add the values to the responses in `tests/api_data.py`
  - regenerate the snapshots and review the new entities
- Patch `dt_util.now` in the module under test for date-dependent values
- Test only through Home Assistant:
  - exception: static checks of files (e.g. `test_translations.py`), with `_`-prefixed helpers in the test module
  - never call, patch or inspect `_`-prefixed methods or attributes of the integration
  - never patch the API library, mock its HTTP requests instead
  - set up the integration and drive it through the mocked HTTP responses
  - trigger updates with `coordinator.async_refresh()`
  - assert entity states, `ConfigEntryState`, the device registry or the requested URLs
- `pytest.mark.parametrize` with `ids=` naming each case
- Constants of a test module in a module with its name and `_data.py` (`test_api.py` → `test_api_data.py`)
  - shared by several test modules: `tests/api_data.py`
