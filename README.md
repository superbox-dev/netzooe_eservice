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

## Installation

[![Open HACS repository on my Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)][redirect-hacs]

1. Install the integration with [HACS](https://hacs.xyz/) (search for "Netz OÖ eService").
2. Restart Home Assistant.
3. Go to **Settings** → **Devices & services**, select **+ Add integration** and search for **Netz OÖ eService**.

Requires Home Assistant 2026.9.4 or newer and an account for the Netz OÖ eService portal. See the
[installation](https://superbox-dev.github.io/netzooe_eservice/#installation) and
[configuration](https://superbox-dev.github.io/netzooe_eservice/#configuration) sections for a manual installation and
all parameters.

[redirect-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=superbox-dev&repository=netzooe_eservice&category=integration

## Documentation

Read the full documentation on [superbox-dev.github.io/netzooe_eservice](https://superbox-dev.github.io/netzooe_eservice/):
[options](https://superbox-dev.github.io/netzooe_eservice/#options),
[sensors](https://superbox-dev.github.io/netzooe_eservice/#supported-functionality),
[examples](https://superbox-dev.github.io/netzooe_eservice/#examples),
[troubleshooting](https://superbox-dev.github.io/netzooe_eservice/#troubleshooting) and more.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Get involved

Contributions are welcome: report [issues](https://github.com/superbox-dev/netzooe_eservice/issues/new/choose),
request features, improve translations or contribute code. Read [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Donation

<!--start-donation-->

I put a lot of time into this project. If you like it, you can support me with a donation.

[![KoFi](https://raw.githubusercontent.com/superbox-dev/.github/refs/heads/main/profile/superbox-kofi.jpg)][kofi]

or [donate with PayPal](https://www.paypal.com/donate?hosted_button_id=34ZFWTH4TNLXS)

[kofi]: https://ko-fi.com/F2F0KXO6D

<!--end-donation-->
