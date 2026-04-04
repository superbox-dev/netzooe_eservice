"""Config flow for Netz OÖ eService."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.error import APIError

from .const import CONFIG_ENTRY_VERSION
from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant
    from .coordinator import NetzOOEeServiceConfigEntry

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, /, *, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    session: ClientSession = async_create_clientsession(hass)
    _LOGGER.debug("Try to connected to the Netz OÖ eService portal")

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


class NetzOOEeServiceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Netz OÖ eService."""

    VERSION: int = CONFIG_ENTRY_VERSION

    def __init__(self) -> None:
        """Initialize flow."""
        self._username: str = ""
        self._entry: NetzOOEeServiceConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None and user_input.get(CONF_USERNAME) and user_input.get(CONF_PASSWORD):
            errors = await self._async_validate_or_error(user_input)

            if not errors:
                return await self._async_complete_entry(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self._username): str,
                    vol.Required(CONF_PASSWORD): str,
                },
            ),
            errors=errors,
            description_placeholders={
                "name": f"{MANUFACTURER} {NAME}",
            },
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        self._entry = self._get_reconfigure_entry()

        self._username = self._entry.data[CONF_USERNAME]

        return await self.async_step_user(user_input)

    async def _async_validate_or_error(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Validate or error."""
        errors: dict[str, str] = {}

        try:
            await validate_input(self.hass, data=user_input)
        except CannotConnectError:
            errors["base"] = "cannot_connect"
        except InvalidAuthError:
            errors["base"] = "invalid_auth"
        except Exception:
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected exception")

        return errors

    async def _async_complete_entry(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(user_input[CONF_USERNAME])

        if self._entry is not None:
            self._abort_if_unique_id_mismatch(
                reason="wrong_account",
                description_placeholders={
                    "name": f"{MANUFACTURER} {NAME}",
                },
            )

            return self.async_update_reload_and_abort(
                self._entry,
                data_updates=user_input,
            )

        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=f"{MANUFACTURER} {NAME} ({user_input[CONF_USERNAME]})", data=user_input)


class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):
    """Error to indicate there is invalid auth."""
