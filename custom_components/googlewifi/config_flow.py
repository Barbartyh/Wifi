"""Config flow for Google Wifi."""
import logging

import voluptuous as vol
from googlewifi import GoogleWifi
from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client, config_entry_flow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import DOMAIN, REFRESH_TOKEN, ADD_DISABLED, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GoogleWifi."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        config_entry = self.hass.config_entries.async_entries(DOMAIN)
        if config_entry:
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            session = aiohttp_client.async_get_clientsession(self.hass)

            token = user_input[REFRESH_TOKEN]
            api_client = GoogleWifi(token, session)

            try:
                await api_client.connect()
            except ValueError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[REFRESH_TOKEN])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Google Wifi", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(REFRESH_TOKEN): str,
                    vol.Required(ADD_DISABLED, default=True): bool,
                }
            ),
            errors=errors,
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow changes."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, POLLING_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=3),
                    ),
                }
            ),
        )
