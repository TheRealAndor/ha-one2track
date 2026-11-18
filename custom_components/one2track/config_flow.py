"""Config flow for the One2Track integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    One2TrackApiClient,
    One2TrackApiClientAuthenticationError,
    One2TrackApiClientCommunicationError,
    One2TrackApiClientError,
)
from .const import DOMAIN, LOGGER

PASSWORD_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
)


class One2TrackConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for One2Track."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors: dict[str, str] = {}

        if user_input is not None:
            account_id = await self._async_try_login(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], _errors
            )
            if account_id:
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"One2Track ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                },
            ),
            errors=_errors,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ) -> config_entries.ConfigFlowResult:
        """Start re-authentication after the stored password stopped working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Ask for the new password and update the existing entry."""
        _errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        username = reauth_entry.data[CONF_USERNAME]

        if user_input is not None:
            account_id = await self._async_try_login(
                username, user_input[CONF_PASSWORD], _errors
            )
            if account_id:
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR}),
            description_placeholders={"username": username},
            errors=_errors,
        )

    async def _async_try_login(
        self, username: str, password: str, errors: dict[str, str]
    ) -> str | None:
        """Test the credentials. Return the account ID, or fill errors and return None."""
        try:
            return await self._test_credentials(username=username, password=password)
        except One2TrackApiClientAuthenticationError as exc:
            LOGGER.warning(exc)
            errors["base"] = "auth"
        except One2TrackApiClientCommunicationError as exc:
            LOGGER.error(exc)
            errors["base"] = "connection"
        except One2TrackApiClientError as exc:
            LOGGER.exception(exc)
            errors["base"] = "unknown"
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Unexpected error during credential test: %s", exc)
            errors["base"] = "unknown"
        return None

    async def _test_credentials(self, username: str, password: str) -> str:
        """Validate credentials and return account_id."""
        client = One2TrackApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        account_id = await client.async_authenticate()
        # Also verify we can discover devices
        await client.async_discover_devices()
        return account_id
