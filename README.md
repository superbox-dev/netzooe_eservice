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

## Documentation

Read the full documentation on [superbox-dev.github.io/netzooe_eservice](https://superbox-dev.github.io/netzooe_eservice/):

- [Configuration](https://superbox-dev.github.io/netzooe_eservice/#configuration) and
  [options](https://superbox-dev.github.io/netzooe_eservice/#options)
- [Supported devices](https://superbox-dev.github.io/netzooe_eservice/#supported-devices) and
  [sensors](https://superbox-dev.github.io/netzooe_eservice/#supported-functionality)
- [Examples](https://superbox-dev.github.io/netzooe_eservice/#examples) and
  [data updates](https://superbox-dev.github.io/netzooe_eservice/#data-updates)
- [Known limitations](https://superbox-dev.github.io/netzooe_eservice/#known-limitations) and
  [troubleshooting](https://superbox-dev.github.io/netzooe_eservice/#troubleshooting)
- [Removing the integration](https://superbox-dev.github.io/netzooe_eservice/#removing-the-integration)

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

<!--start-donation-->

I put a lot of time into this project. If you like it, you can support me with a donation.

[![KoFi](https://raw.githubusercontent.com/superbox-dev/.github/refs/heads/main/profile/superbox-kofi.jpg)][kofi]

or [donate with PayPal](https://www.paypal.com/donate?hosted_button_id=34ZFWTH4TNLXS)

[kofi]: https://ko-fi.com/F2F0KXO6D

<!--end-donation-->
