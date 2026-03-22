import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import *

DEVICE_CLASSES = [
    "temperature", "humidity", "pressure",
    "power", "current", "voltage",
    "battery", "signal_strength",
]

STATE_CLASSES = [
    "measurement", "total", "total_increasing",
]


class AnalogScalerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            if user_input[CONF_MAX_ANALOG] == user_input[CONF_MIN_ANALOG]:
                errors["base"] = "analog_range_invalid"
            elif user_input[CONF_MAX_LIMIT] == user_input[CONF_MIN_LIMIT]:
                errors["base"] = "output_range_invalid"

            if not errors:
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(user_input),
            errors=errors,
            description_placeholders=self._preview(user_input)
        )

    def _get_schema(self, user_input):
        return vol.Schema({
            vol.Required("name", default=(user_input or {}).get("name", "Analog Scaler")): str,

            vol.Required(CONF_SOURCE): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),

            vol.Required(CONF_MIN_ANALOG, default=0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=1)
            ),

            vol.Required(CONF_MAX_ANALOG, default=27648): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=1)
            ),

            vol.Required(CONF_MIN_LIMIT, default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=0.1)
            ),

            vol.Required(CONF_MAX_LIMIT, default=100.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=0.1)
            ),

            vol.Optional(CONF_UNIT): selector.TextSelector(),

            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DEVICE_CLASSES)
            ),

            vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=STATE_CLASSES)
            ),
        })

    def _preview(self, user_input):
        """Live preview af scaling"""
        if not user_input:
            return {"preview": "Indtast værdier for preview"}

        try:
            current = 12345  # demo værdi (kan senere gøres dynamisk)
            min_a = user_input.get(CONF_MIN_ANALOG, 0)
            max_a = user_input.get(CONF_MAX_ANALOG, 1)
            min_l = user_input.get(CONF_MIN_LIMIT, 0)
            max_l = user_input.get(CONF_MAX_LIMIT, 1)

            if max_a == min_a:
                return {"preview": "Ugyldigt range"}

            norm = (current - min_a) / (max_a - min_a)
            norm = max(0.0, min(1.0, norm))
            scaled = norm * (max_l - min_l) + min_l

            return {"preview": f"Eksempel: {current} → {round(scaled,2)}"}

        except Exception:
            return {"preview": "Preview fejl"}

    @staticmethod
    def async_get_options_flow(entry):
        return AnalogScalerOptionsFlow(entry)


class AnalogScalerOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self._entry = entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_schema(),
            errors=errors
        )

    def _get_schema(self):
        data = self._entry.data

        return vol.Schema({
            vol.Optional(CONF_MIN_ANALOG, default=data.get(CONF_MIN_ANALOG)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=1)
            ),
            vol.Optional(CONF_MAX_ANALOG, default=data.get(CONF_MAX_ANALOG)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=1)
            ),
            vol.Optional(CONF_MIN_LIMIT, default=data.get(CONF_MIN_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=0.1)
            ),
            vol.Optional(CONF_MAX_LIMIT, default=data.get(CONF_MAX_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-100000, max=100000, step=0.1)
            ),
        })
        
