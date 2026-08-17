# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-08-17

### Added

- Add "Show revoked energy communities" option. Disabled by default. When enabled, revoked energy communities are
  shown as separate devices with their own sensors, and their values are included in the total sensors.
  [(Issue #21)][issue-21]
- Add "Include data from inactive contract accounts (same meter point)" option. Enabled by default. When disabled,
  data from contract accounts with inactive suppliers at the same meter point is no longer merged into the active
  account's data, including the total import/export sensors. [(Issue #22)][issue-22]
- Add "Show inactive meter points" option. Disabled by default. When enabled, meter points where all contract
  accounts are inactive are also shown as devices with their own sensors, using the most recently ended contract's
  data. [(Issue #22)][issue-22]

[issue-21]: https://github.com/superbox-dev/netzooe_eservice/issues/21
[issue-22]: https://github.com/superbox-dev/netzooe_eservice/issues/22

## [1.0.1] - 2026-08-03

### Fixed

- Fix the issue where meter points with non-active contracts trigger an exception.
  Thank you [fabSteininger](https://github.com/fabSteininger) for your contribution. [(PR #19)][pr-19]

[pr-19]: https://github.com/superbox-dev/netzooe_eservice/pull/19

## [1.0.0] - 2026-05-30

Initial release
