# Tests

- Every new code path needs a test
- Mock HTTP with the `fake_api` fixture (`tests/conftest.py`), responses in `tests/api_data.py`
- Assert entities with snapshots in `tests/snapshots/`
- New entity:
  - add the values to the responses in `tests/api_data.py`
  - regenerate the snapshots and review the new entities
- Patch `dt_util.now` in the module under test for date-dependent values
- Test only through Home Assistant:
  - never call, patch or inspect `_`-prefixed methods or attributes, or the API library
  - set up the integration and drive it through the mocked HTTP responses
  - trigger updates with `coordinator.async_refresh()`
  - assert entity states, `ConfigEntryState`, the device registry or the requested URLs
