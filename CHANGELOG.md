# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added sensors for the maximum import and export power from the previous month.
- Added the "Frequent updates" option. Disabled by default. When enabled, the energy community contribution
  factors and statuses are refreshed every 15 minutes, while the full data refresh stays at 3-hour intervals.

### Changed

- Updated `netzooe_eservice_api` to 1.1.2b1. Timeouts and unexpected HTTP status codes of the portal are now handled
  as API errors, so the previous data is kept instead of failing the update.
- Renamed "(letzter Monat)" to "(Vormonat)" in the German sensor names. Existing entity IDs are not changed.
- Documented the options and update intervals in the README.

### Fixed

- Fixed the "Open HACS repository" link in the README.

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
