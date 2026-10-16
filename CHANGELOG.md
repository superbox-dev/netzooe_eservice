# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added sensors for the maximum import and export power from the previous month.
- Added the "Frequent updates" option. Disabled by default. When enabled, the energy community contribution
  factors and statuses are refreshed every 15 minutes, while the full data refresh stays at 3-hour intervals.
- Added reauthentication. If the portal rejects the credentials, Home Assistant now asks for the new password.
- Added diagnostics. Credentials and customer numbers are removed.
- Added the sensors of new meter points and energy communities after an update, without reloading the integration.

### Changed

- Updated `netzooe_eservice_api` to 1.1.2b1. Timeouts and unexpected HTTP status codes of the portal are now handled
  as API errors, so the previous data is kept instead of failing the update.
- Renamed "(letzter Monat)" to "(Vormonat)" in the German sensor names. Existing entity IDs are not changed.
- Documented the options and update intervals in the README.
- Requested the contract accounts and consumption profiles in parallel (at most 4 requests at the same time), which
  makes a full update about 3 times faster.
- Fetched the dashboard on every full update, so the contract accounts are no longer only read at startup.
- Logged API errors with cached data as a single warning instead of an error and a warning.
- Logged API errors with cached data only once until the portal is available again.
- Changed the `status` sensor to an enum sensor with translated states. Unknown statuses are shown as unknown.
- Moved the sensor icons to `icons.json`.
- Translated the error message if the first update fails.
- Documented the installation parameters, sensors, use cases, known limitations, troubleshooting and removal in the
  README.

### Fixed

- Fixed the "Open HACS repository" link in the README.
- Fixed `supplier_export_l3` of the meter point, which showed the total generation instead of the supplier export
  of all energy communities.
- Fixed the `status` sensor failing if the portal returns a consent without a status.
- Fixed the "already configured" message and added the missing "wrong account" message of the config flow.

## [1.1.1] - 2026-09-28

### Changed

- Required Home Assistant 2026.9.4 or newer.

### Fixed

- Fixed Home Assistant device registry compatibility by replacing the deprecated `via_device` with `via_device_id`.
- Fixed meter reading selection when the API returns multiple registers for the same meter. Energy readings are now
  selected by the valid OBIS references 1.8.1 or 2.8.1 instead of relying on the order returned
  by the API. ([Issue #25][issue-25])

## [1.1.0] - 2026-08-17

### Added

- Added the "Show revoked energy communities" option. Disabled by default. When enabled, revoked energy communities
  are shown as separate devices with their own sensors, and their values are included in the total sensors.
  ([Issue #21][issue-21])
- Added the "Include data from inactive contract accounts (same meter point)" option. Enabled by default. When
  disabled, data from contract accounts with inactive suppliers at the same meter point is no longer merged into the
  active account's data, including the total import/export sensors. ([Issue #20][issue-20])
- Added the "Show inactive meter points" option. Disabled by default. When enabled, meter points where all contract
  accounts are inactive are also shown as devices with their own sensors, using the most recently ended contract's
  data. ([Issue #20][issue-20])
- Added automatic removal of devices that are no longer returned by the API, e.g. after changing an option.

### Changed

- Required Home Assistant 2026.7.0 or newer.
- Updated `netzooe_eservice_api` to 1.1.1.

## [1.0.1] - 2026-08-03

### Fixed

- Fixed the issue where meter points with non-active contracts triggered an exception.
  Thank you [fabSteininger](https://github.com/fabSteininger) for your contribution. ([PR #19][pr-19])

## [1.0.0] - 2026-05-30

Initial release

[Unreleased]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/superbox-dev/netzooe_eservice/releases/tag/v1.0.0
[issue-20]: https://github.com/superbox-dev/netzooe_eservice/issues/20
[issue-21]: https://github.com/superbox-dev/netzooe_eservice/issues/21
[issue-25]: https://github.com/superbox-dev/netzooe_eservice/issues/25
[pr-19]: https://github.com/superbox-dev/netzooe_eservice/pull/19
