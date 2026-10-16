# Netz OÖ eService

[![CI](https://github.com/superbox-dev/netzooe_eservice/actions/workflows/ci.yml/badge.svg?branch=main)][workflow-ci]
![coverage-badge](https://raw.githubusercontent.com/superbox-dev/netzooe_eservice/main/coverage-badge.svg)
![Typing: strict][typing-strict]
![Code style: Ruff][code-ruff]

A Home Assistant integration to read energy data from the [Netz OÖ eService portal](https://eservice.netzooe.at).

> [!NOTE]
> This is an unofficial integration. It is not affiliated with or supported by Netz Oberösterreich GmbH.

![dashboard.png](assets/dashboard.png)

[workflow-ci]: https://github.com/superbox-dev/netzooe_eservice/actions/workflows/ci.yml
[typing-strict]: https://img.shields.io/badge/typing-strict-green.svg
[code-ruff]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json

## Requirements

- Home Assistant 2026.9.4 or newer with [HACS](https://hacs.xyz/) installed.
- An account for the Netz OÖ eService portal.

## Installation

[![Open HACS repository on my Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)][redirect-hacs]

1. Install this integration with HACS (search for "Netz OÖ eService"). For a manual installation, copy the
   `custom_components/netzooe_eservice` directory into the `custom_components` directory of your Home Assistant
   configuration.
2. Restart Home Assistant.
3. Go to **Settings** → **Devices & services**, click **+ Add integration** and select **Netz OÖ eService**.
4. Enter the username and password of your Netz OÖ eService portal account.

| Parameter | Description                                                                    |
|-----------|--------------------------------------------------------------------------------|
| Username  | The username of your Netz OÖ eService portal account, e.g. your email address. |
| Password  | The password of your Netz OÖ eService portal account.                          |

To change the credentials later, select **Reconfigure** in the integration's menu. If the portal rejects the
credentials, e.g. after a password change, Home Assistant asks you to enter the new password.

[redirect-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=superbox-dev&repository=netzooe_eservice&category=integration

## Options

Open **Settings** → **Devices & services** → **Netz OÖ eService** → **Configure** to change these options:

| Option                                                          | Default  | Description                                                                                                                               |
|-----------------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Frequent updates (every 15 minutes)                             | Disabled | Refresh the energy community contribution factors and statuses every 15 minutes. When disabled, all data is refreshed every 3 hours only. |
| Show revoked energy communities                                 | Disabled | Show revoked energy communities as separate devices and include their values in the total sensors.                                        |
| Include data from inactive contract accounts (same meter point) | Enabled  | Merge data from contract accounts with inactive suppliers at the same meter point into the active account's data.                         |
| Show inactive meter points                                      | Disabled | Show meter points where all contract accounts are inactive, using the data of the most recently ended contract.                           |

## Data updates

All data is refreshed every 3 hours. With **Frequent updates** enabled, the contribution factors and statuses of
the energy communities are additionally refreshed every 15 minutes.

Sensors marked with "16-day delay" contain values that the portal only provides with a delay of about 16 days.

## Supported devices

The integration creates a device for each electricity meter point of your account:

- **Household** (Haushalt): meter point that imports energy from the grid
- **Photovoltaics** (Photovoltaik): meter point that exports energy to the grid

Each energy community (Energiegemeinschaft) that a meter point takes part in gets its own device, linked to the
device of the meter point.

## Sensors

Meter point:

| Sensor                                            | Description                                                                         |
|---------------------------------------------------|-------------------------------------------------------------------------------------|
| Meter reading                                     | Last meter reading in kWh                                                           |
| Maximum Import/Export Power (previous month)      | Peak power of the previous month in kW                                              |
| Monthly/Yearly trend (current/previous period)    | Energy of the current and previous period in kWh                                    |
| Monthly/Yearly trend                              | Change between the current and previous period in %                                 |
| Supplier                                          | Name of the energy supplier                                                         |
| Type                                              | Type of the meter point, e.g. "EEG 7ngem"                                           |
| Energy community / Supplier import/export (total) | Total of all energy communities of the meter point (disabled by default, see below) |

Energy community:

| Sensor                                          | Description                                                                 |
|-------------------------------------------------|-----------------------------------------------------------------------------|
| Energy community import/export L1/L2/L3         | Energy shared with the energy community, including the most recent L3 data  |
| Energy community import/export L1/L2            | Energy shared with the energy community, final values (16-day delay)        |
| Energy community import/export L2 (prev. month) | Energy shared with the energy community in the previous month               |
| Supplier import/export L1/L2/L3, L1/L2, L2      | Energy imported from or exported to the energy supplier for the same ranges |
| Contribution factor                             | Contribution factor (Teilnahmefaktor) of the meter point in %               |
| Status                                          | Status of the participation: active, active (unchangeable) or revoked       |

The total sensors of the meter point are disabled by default. Enable them in the entity settings if your meter
point takes part in several energy communities. They only include energy communities with the status "active",
unless **Show revoked energy communities** is enabled.

## Known limitations

- The portal provides the L1/L2 values of the energy communities with a delay of about 16 days. Sensors with
  "16-day delay" in their name only contain these final values.
- The meter readings and trends are only updated by the portal once a day.
- If the portal is not available, the sensors keep their last values until the next successful update.

## Troubleshooting

- **Invalid authentication**: check that you can log in to the [eService portal](https://eservice.netzooe.at) with
  the same username and password.
- **Failed to connect**: the portal may be in maintenance. Home Assistant retries the setup automatically.
- **Missing energy community**: the energy community is only shown if the portal returns a consent for it. Revoked
  energy communities are hidden, unless **Show revoked energy communities** is enabled.
- **Missing meter point**: meter points without an active contract are hidden, unless
  **Show inactive meter points** is enabled.

If the problem persists, [enable debug logging][debug-logs], reproduce the problem and open an
[issue](https://github.com/superbox-dev/netzooe_eservice/issues/new/choose) with the log and the
[diagnostics][diagnostics] of the integration. Credentials and customer numbers are removed from the diagnostics.

[debug-logs]: https://www.home-assistant.io/docs/configuration/troubleshooting/#debug-logs-and-diagnostics
[diagnostics]: https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics

## Removal

1. Go to **Settings** → **Devices & services** and select **Netz OÖ eService**.
2. Click the three dots of the entry and select **Delete**.
3. To remove the files as well, remove the integration in HACS and restart Home Assistant.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Get involved

The **Netz OÖ eService** integration is an open-source project and contributions are welcome. You can:

- Report [issues](https://github.com/superbox-dev/netzooe_eservice/issues/new/choose) or request new features
- Improve documentation or translations
- Contribute code
- Support the project by starring it on GitHub ⭐

Read [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Donation

I put a lot of time into this project. If you like it, you can support me with a donation.

[![KoFi](https://raw.githubusercontent.com/superbox-dev/.github/refs/heads/main/profile/superbox-kofi.jpg)][kofi]

or [donate with PayPal](https://www.paypal.com/donate?hosted_button_id=34ZFWTH4TNLXS)

[kofi]: https://ko-fi.com/F2F0KXO6D
