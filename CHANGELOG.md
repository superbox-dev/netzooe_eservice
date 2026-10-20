# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!--start-->

### Changed

- Showed the documentation in the light mode by default and kept the right column readable on smaller screens.

### Fixed

- Fixed the "Include data from inactive contract accounts" option being ignored for meter points without an active
  contract. When disabled, their energy communities now only use the most recently ended contract instead of all
  contracts of the meter point.
- Updated `netzooe_eservice_api` to 1.2.1b2. Unloading the integration while a login is still running no longer
  fails with an unexpected error.
- Fixed the error `Detected code that closes the Home Assistant aiohttp session` that was logged each time the
  integration was unloaded or reloaded, e.g. after changing the options.

### Security

- Redacted the business partner, contract account, meter and meter point numbers in the debug log of the portal
  data.

## [1.2.0] - 2026-10-18

### Added

- Added sensors for the maximum import and export power from the previous month.
- Added the diagnostic sensor "Profile data available until" with the last day of profile data of a meter point.
- Added the market partner ID of the energy supplier and the contract start as attributes `id` and `contract_start`
  to the `supplier` sensor.
- Added the start date of the consent as attribute `valid_from` to the `status` sensor of an energy community.
- Added the "Frequent updates" option. Disabled by default. When enabled, the energy community contribution
  factors and statuses are refreshed every 15 minutes, while the full data refresh stays at 3-hour intervals.
- Added reauthentication. If the portal rejects the credentials, Home Assistant now asks for the new password.
- Added diagnostics. Credentials and customer numbers are removed.
- Added the sensors of new meter points and energy communities after an update, without reloading the integration.
- Added the "wrong account" message to the reconfiguration flow.
- Added the documentation with Docusaurus on GitHub Pages (<https://superbox-dev.github.io/netzooe_eservice/>),
  styled after the integration pages of Home Assistant, with an example automation.
- Added a preview image to the documentation for links shared on social media and removed the search page
  from the documentation sitemap.

### Changed

- Updated `netzooe_eservice_api` to 1.2.0. Timeouts and unexpected HTTP status codes of the portal are now handled
  as API errors, so the previous data is kept instead of failing the update.
- Renamed "(letzter Monat)" to "(Vormonat)" in the German sensor names and "(last month)" to "(previous month)" in
  the English sensor names. Existing entity IDs are not changed.
- Requested the contract accounts and consumption profiles in parallel (at most 4 requests at the same time), which
  makes a full update about 3 times faster.
- Cancelled the remaining requests of an update if one request fails, so rejected credentials no longer cause
  further login attempts.
- Fetched the dashboard on every full update, so the contract accounts are no longer only read at startup.
- Logged API errors with cached data as a single warning, and only once until the portal is available again.
- Changed the `status` sensor to an enum sensor with translated states, including `requested`, `qr_code_sent`,
  `timeout` and `concluded`. Unknown statuses are shown as unknown.
- Moved the sensor icons to `icons.json`.
- Translated the error message if the first update fails.
- Documented the installation parameters, options, update intervals, sensors, use cases, known limitations,
  troubleshooting and removal in the README.
- Shortened the `README.md` to the installation and moved the details to the documentation.
- Changed the `documentation` link in `manifest.json` to the documentation.
- Changed the reauthentication to only ask for the new password of the configured account.
- Gave the reconfiguration flow its own form with a matching description.
- Excluded the `timeline` attribute from the recorder database, because it grows with every timeslice.
- Logged a meter point without an active contract only once until it has an active contract again.

### Fixed

- Fixed the "Open HACS repository" link in the README.
- Fixed `supplier_export_l3` of the meter point, which showed the total generation instead of the supplier export
  of all energy communities.
- Fixed the `status` sensor failing if the portal returns a consent without a status.
- Fixed the update failing if the portal returns an energy community without a consent. The energy community is now
  skipped and a warning is logged once.
- Fixed energy communities getting the consent of another service provider whose code also appears in their ID.
- Fixed the "already configured" message of the config flow.
- Fixed the options not being changeable while the integration is not loaded.
- Fixed the HTTP session of each login attempt in the config flow staying open until Home Assistant stops.
- Fixed the HTTP session of the integration staying open until Home Assistant stops after a reload, e.g. after
  changing the options or reauthenticating.

## [1.1.1] - 2026-09-28

### Changed

- Required Home Assistant 2026.9.4 or newer.

### Fixed

- Fixed Home Assistant device registry compatibility by replacing the deprecated `via_device` with `via_device_id`.
- Fixed meter reading selection when the API returns multiple registers for the same meter. Energy readings are now
  selected by the valid OBIS references 1.8.1 or 2.8.1 instead of relying on the order returned
  by the API. ([Issue #25][issue-25])

[issue-25]: https://github.com/superbox-dev/netzooe_eservice/issues/25

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

[issue-20]: https://github.com/superbox-dev/netzooe_eservice/issues/20
[issue-21]: https://github.com/superbox-dev/netzooe_eservice/issues/21

## [1.0.1] - 2026-08-03

### Fixed

- Fixed the update failing if a meter point has no active contract. Its contracts are now skipped and a warning is
  logged. Thank you [fabSteininger](https://github.com/fabSteininger) for your contribution. ([PR #19][pr-19])

[pr-19]: https://github.com/superbox-dev/netzooe_eservice/pull/19

## [1.0.0] - 2026-05-30

### Added

- Added the config flow with the username and password of the eService portal, and the reconfiguration flow.
- Added a device for each meter point and for each energy community of a meter point.
- Added the meter point sensors: type, meter reading, supplier, monthly and yearly trend (current and previous
  period), energy community import or export (L2, L3 and previous month), supplier import or export (L2, L3 and
  previous month).
- Added the energy community sensors: status, contribution factor, energy community import or export and supplier
  import or export (L2, L3 and previous month).
- Added English and German translations.
- Added the data update every 3 hours.

[Unreleased]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/superbox-dev/netzooe_eservice/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/superbox-dev/netzooe_eservice/releases/tag/v1.0.0

<!--end-->
