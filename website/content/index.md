---
sidebar_position: 0
sidebar_label: Integration
slug: /
title: Home Assistant integration for Netz OÖ eService
description: >-
  Show the meter readings, consumption trends, peak power and energy communities of your electricity meter points
  from the Netz OÖ eService portal in Home Assistant.
---

The **Netz OÖ eService** integration reads the energy data of your electricity meter points from the
[Netz OÖ eService portal](https://eservice.netzooe.at). Netz Oberösterreich is the grid operator in Upper Austria.

The integration provides:

- the meter readings
- the monthly and yearly consumption trends
- the peak power of the previous month
- the L1 profile data of the meter point
- the energy shared with your energy communities (Energiegemeinschaften)

:::note[Unofficial integration]

This is an unofficial community integration. It is not affiliated with or supported by Netz Oberösterreich GmbH.
For support, open an [issue](https://github.com/superbox-dev/netzooe_eservice/issues/new/choose). Do not contact
Netz Oberösterreich.

:::

![Dashboard with the sensors of a meter point and its energy communities](../../assets/dashboard.png)

## Use cases

- Show the meter reading and the consumption of the current and previous month or year on a dashboard.
- See how much of your consumption comes from your energy community and how much from your supplier.
- Track how much energy your photovoltaics system shares with the energy community.
- Get notified when the participation in an energy community changes, e.g. when it is revoked.
- Check the peak power of the previous month, e.g. to plan a heat pump or a wallbox.

## Supported devices

| Device           | Description                                                         |
|------------------|---------------------------------------------------------------------|
| Household        | Meter point that imports energy from the grid (Haushalt)            |
| Photovoltaics    | Meter point that exports energy to the grid (Photovoltaik)          |
| Energy community | One device per energy community, linked to the meter point's device |

## Prerequisites

- Home Assistant 2026.9.4 or newer.
- An account for the [Netz OÖ eService portal](https://eservice.netzooe.at).
- Log in once in the browser and check that your meter points are shown there.

## Installation

[![Open the repository in the Marketplace of your Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)][redirect-hacs]

1. Go to **Settings** → **Marketplace**.
2. Search for **Netz OÖ eService** and select **Install**.
3. Follow the setup that starts after the installation.

[redirect-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=superbox-dev&repository=netzooe_eservice&category=integration

## Configuration

To add the integration to your Home Assistant instance, use this My button:

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)][redirect-config-flow]

Or go to **Settings** → **Devices & services**, select **+ Add integration** and search for **Netz OÖ eService**.

| Parameter | Description                                                       |
|-----------|-------------------------------------------------------------------|
| Username  | Username of your eService portal account, e.g. your email address |
| Password  | Password of your eService portal account                          |

- To change the credentials, select **Reconfigure** in the menu of the integration entry.
- If the portal rejects the credentials, e.g. after a password change, Home Assistant asks for the new password.

[redirect-config-flow]: https://my.home-assistant.io/redirect/config_flow_start/?domain=netzooe_eservice

## Options

Go to **Settings** → **Devices & services** → **Netz OÖ eService** and select **Configure**.

| Option                                                          | Default  | Description                                                                                  |
|-----------------------------------------------------------------|----------|----------------------------------------------------------------------------------------------|
| Frequent updates (every 15 minutes)                             | Disabled | Refreshes the contribution factors and statuses of the energy communities every 15 minutes   |
| Show revoked energy communities                                 | Disabled | Shows revoked energy communities as devices and includes them in the total sensors           |
| Include data from inactive contract accounts (same meter point) | Enabled  | Adds the data of former contract accounts at the same meter point, e.g. of a former supplier |
| Show inactive meter points                                      | Disabled | Shows meter points without an active contract, with the data of the last contract            |

Without **Frequent updates**, all data is refreshed every 3 hours.

## Supported functionality

### Sensors of a meter point

| Sensor                                            | Description                                                         |
|---------------------------------------------------|---------------------------------------------------------------------|
| Meter reading                                     | Last meter reading in kWh                                           |
| Maximum Import/Export Power (previous month)      | Peak power of the previous month in kW                              |
| Monthly/Yearly trend (current/previous period)    | Energy of the current and previous period in kWh                    |
| Monthly/Yearly trend                              | Change between the current and previous period in %                 |
| Supplier                                          | Supplier name, market partner ID in `id`, start in `contract_start` |
| Type                                              | Type of the meter point, e.g. "EEG 7ngem"                           |
| Profile data available until                      | Last day with profile data in the portal (diagnostic)               |
| Energy community / Supplier import/export (total) | Total of all energy communities (disabled by default, see below)    |
| Import/Export L1                                  | Energy of all profile data in kWh                                   |
| Import/Export L1 (previous month)                 | Energy of the previous calendar month in kWh                        |
| Import/Export L1 (last day)                       | Energy of the last day with data (usually yesterday) in kWh         |

#### L1 sensors

- They include all contracts of the meter point.
- Inactive contract accounts only count if **Include data from inactive contract accounts** is enabled.
- They are unavailable if the portal has no profile data for their time range.
- The state is the sum of all sections.

The `timeline` attribute has one entry per section of the profile. A section is like a "Zählpunktinformationen"
box in the portal. A new section starts e.g. after a change from daily to quarter-hourly values.

| Attribute                                | Description                                           |
|------------------------------------------|-------------------------------------------------------|
| `from`, `to`                             | First and last day of the section                     |
| `resolution`                             | Resolution of the values, e.g. `year`, `month`, `day` |
| `sum`                                    | Energy of the section in kWh                          |
| `average`                                | Average energy per resolution in kWh                  |
| `maximum`, `minimum`                     | Highest and lowest energy per resolution in kWh       |
| `maximum_timestamp`, `minimum_timestamp` | Start of the highest and lowest value in local time   |

The portal chooses the resolution from the length of the time range:

| Sensor           | Resolution                              |
|------------------|-----------------------------------------|
| All profile data | `year` (`month` if the data is shorter) |
| Previous month   | `day`                                   |
| Last day         | `quarter_of_an_hour`                    |

This timeline is small. It is recorded in the database, so the values stay in the history.

#### Total sensors

- The energy community and supplier totals are disabled by default.
- Enable them in the entity settings if your meter point takes part in several energy communities.
- They only include energy communities with the status "active", unless **Show revoked energy communities** is
  enabled.
- They have no `timeline` attribute.

### Sensors of an energy community

| Sensor                                          | Description                                                          |
|-------------------------------------------------|----------------------------------------------------------------------|
| Energy community import/export L1/L2/L3         | Energy shared with the energy community, with the latest L3 data     |
| Energy community import/export L1/L2            | Energy shared with the energy community, final values (16-day delay) |
| Energy community import/export L2 (prev. month) | Energy shared with the energy community in the previous month        |
| Supplier import/export L1/L2/L3, L1/L2, L2      | Energy from or to the energy supplier, for the same time ranges      |
| Contribution factor                             | Contribution factor (Teilnahmefaktor) of the meter point in %        |
| Status                                          | Participation status, e.g. active or revoked, start in `valid_from`  |

The energy sensors count the energy since the start of the participation.

The `timeline` attribute has one entry per timeslice of the energy community:

- Every entry has `from` and `to`.
- **Energy community import** and **Supplier export** also have `resolution`, `sum`, `average`, `maximum`,
  `minimum` and the timestamps. They are the same attributes as for the L1 sensors.
- **Supplier import** and **Energy community export** only have `from` and `to`. They are the difference of two
  values of the portal, and the portal returns no average, maximum or minimum for a difference.
- Each timeslice is requested separately, so the resolution can differ between entries, e.g. `day` for the previous
  month and `month` or `year` for the totals.
- This timeline grows with every timeslice. It is not recorded in the database.

## Examples

The entity IDs consist of:

1. `sensor.netzooe_eservice_`
2. the meter point number
3. the energy community ID (only for sensors of an energy community)
4. the sensor key

Replace the ID in the examples with the one of your device. You find it in the entity settings.

### Maximum of the last day

This template returns the highest quarter-hourly value of the last day with data:

```jinja
{% set entity_id = 'sensor.netzooe_eservice_at0000000000000000000000000000001_last_day_import_l1' %}
{{ state_attr(entity_id, 'timeline')[-1].maximum }}
```

### Notification when a participation ends

This automation sends a notification when the status of an energy community changes from active to another status,
e.g. revoked:

```yaml
automation:
  - alias: "Energy community participation changed"
    triggers:
      - trigger: state
        entity_id: sensor.netzooe_eservice_at0000000000000000000000000000001_cc100001_status
        from: "active"
    conditions:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable'] }}"
    actions:
      - action: notify.notify
        data:
          title: "Energy community"
          message: >
            The status of {{ device_attr(trigger.entity_id, 'name') }}
            is now {{ state_translated(trigger.entity_id) }}.
```

## Data updates

| Update                        | Interval         | Data                                                        |
|-------------------------------|------------------|-------------------------------------------------------------|
| Full update                   | Every 3 hours    | All data                                                    |
| Frequent updates (if enabled) | Every 15 minutes | Contribution factors and statuses of the energy communities |

- The requests of an update run in parallel, at most 4 at the same time.
- New meter points and energy communities are added after an update, without a restart.
- Devices that the portal no longer returns are removed.

## Known limitations

- The portal provides the L1/L2 values of the energy communities with a delay of about 16 days. Sensors with
  "16-day delay" in their name only contain these final values.
- The portal updates the meter readings and trends only once a day.
- The L1 profile data is usually available up to yesterday. The L1 sensors show the last complete day and the
  previous month, not today.
- If the portal is not available, the sensors keep their last values until the next successful update.
- The portal is not designed for automated access. The integration can stop working if Netz Oberösterreich changes
  the portal.

## Troubleshooting

| Problem                  | Solution                                                                                                  |
|--------------------------|-----------------------------------------------------------------------------------------------------------|
| Invalid authentication   | Check that you can log in to the [eService portal](https://eservice.netzooe.at) with the same credentials |
| Failed to connect        | The portal may be in maintenance. Home Assistant retries the setup automatically                          |
| Missing energy community | It is only shown if the portal returns a consent. Revoked ones need **Show revoked energy communities**   |
| Missing meter point      | Meter points without an active contract need **Show inactive meter points**                               |

If the problem persists:

1. [Enable debug logging][debug-logs].
2. Reproduce the problem.
3. Open an [issue](https://github.com/superbox-dev/netzooe_eservice/issues/new/choose) with the log and the
   [diagnostics][diagnostics] of the integration.

Credentials and customer numbers are removed from the diagnostics.

[debug-logs]: https://www.home-assistant.io/docs/configuration/troubleshooting/#debug-logs-and-diagnostics
[diagnostics]: https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics

## Removing the integration

This integration follows standard integration removal.

1. Go to **Settings** → **Devices & services** and select **Netz OÖ eService**.
2. Select the three dots ⋮ of the entry and select **Delete**.
3. To remove the files as well, remove the integration in the Marketplace and restart Home Assistant.
