import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import *

DEVICE_CLASSES = [
    "temperature",
    "humidity",
    "pressure",
    "power",
    "current",
    "voltage",
    "battery",
    "signal_strength",
]

STATE_CLASSES = [
    "measurement",
    "total",
    "total_increasing",
]

class AnalogScalerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Analog Scaler",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(CONF_SOURCE): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_MIN_ANALOG, default=0): int,
            vol.Required(CONF_MAX_ANALOG, default=27648): int,
            vol.Required(CONF_MIN_LIMIT, default=0.0): float,
            vol.Required(CONF_MAX_LIMIT, default=100.0): float,

            vol.Optional(CONF_UNIT): str,

            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DEVICE_CLASSES)
            ),

            vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=STATE_CLASSES)
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema)
