# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Config flow for Netz OÖ eService."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import probatio as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import BooleanSelector
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.error import APIError

from .const import CONF_FREQUENT_UPDATES
from .const import CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from .const import CONF_SHOW_INACTIVE_METER_POINTS
from .const import CONF_SHOW_REVOKED_ENERGY_COMMUNITIES
from .const import CONFIG_ENTRY_VERSION
from .const import DEFAULT_FREQUENT_UPDATES
from .const import DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from .const import DEFAULT_SHOW_INACTIVE_METER_POINTS
from .const import DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES
from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

    from .coordinator import NetzOOEeServiceConfigEntry

_LOGGER = logging.getLogger(__name__)

# Options with their defaults, in the order of the options form.
OPTIONS: Final[dict[str, bool]] = {
    CONF_FREQUENT_UPDATES: DEFAULT_FREQUENT_UPDATES,
    CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES,
    CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA,
    CONF_SHOW_INACTIVE_METER_POINTS: DEFAULT_SHOW_INACTIVE_METER_POINTS,
}
DESCRIPTION_PLACEHOLDERS: Final[dict[str, str]] = {
    "name": f"{MANUFACTURER} {NAME}",
}


async def validate_input(hass: HomeAssistant, /, *, data: Mapping[str, Any]) -> None:
    """Validate that the credentials can log in to the eService portal."""
    # The session is only needed for this login, so it is detached afterwards instead of on shutdown.
    session: ClientSession = async_create_clientsession(hass, auto_cleanup=False)
    _LOGGER.debug("Try to connect to the Netz OÖ eService portal")

    client: NetzOOEeServiceAPI = NetzOOEeServiceAPI(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        session=session,
    )

    try:
        await client.dashboard()
    except APIError as error:
        _LOGGER.debug("API error %s", error)
        if error.status == HTTPStatus.UNAUTHORIZED:
            raise InvalidAuthError from error

        raise CannotConnectError from error
    else:
        _LOGGER.debug("Connected to the Netz OÖ eService portal")
    finally:
        session.detach()


class NetzOOEeServiceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Netz OÖ eService."""

    VERSION: int = CONFIG_ENTRY_VERSION

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()
            errors = await self._async_validate_or_error(user_input)

            if not errors:
                return self.async_create_entry(
                    title=f"{MANUFACTURER} {NAME} ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._credentials_schema(username=user_input[CONF_USERNAME] if user_input else ""),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration of the credentials."""
        entry: NetzOOEeServiceConfigEntry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_mismatch(reason="wrong_account", description_placeholders=DESCRIPTION_PLACEHOLDERS)
            errors = await self._async_validate_or_error(user_input)

            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._credentials_schema(username=entry.data[CONF_USERNAME]),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Handle reauthentication if the portal rejects the credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the new password of the configured account."""
        entry: NetzOOEeServiceConfigEntry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate_or_error(entry.data | user_input)

            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS | {CONF_USERNAME: entry.data[CONF_USERNAME]},
        )

    @staticmethod
    def _credentials_schema(*, username: str) -> vol.Schema:
        """Return the schema of the username and password form."""
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=username): str,
                vol.Required(CONF_PASSWORD): str,
            },
        )

    async def _async_validate_or_error(self, data: Mapping[str, Any]) -> dict[str, str]:
        """Validate the credentials and return the errors for the form."""
        errors: dict[str, str] = {}

        try:
            await validate_input(self.hass, data=data)
        except CannotConnectError:
            errors["base"] = "cannot_connect"
        except InvalidAuthError:
            errors["base"] = "invalid_auth"
        except Exception:
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected exception")

        return errors

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: NetzOOEeServiceConfigEntry,  # noqa: ARG004
    ) -> NetzOOEeServiceOptionsFlow:
        """Get the options flow for this handler."""
        return NetzOOEeServiceOptionsFlow()


class NetzOOEeServiceOptionsFlow(OptionsFlowWithReload):
    """Option flow for Netz OÖ eService."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(option, default=self.config_entry.options.get(option, default)): BooleanSelector()
                    for option, default in OPTIONS.items()
                },
            ),
        )


class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):
    """Error to indicate there is invalid auth."""
