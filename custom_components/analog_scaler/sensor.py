from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import *

AUTO_MAPPINGS = {
    "%": {"device_class": "humidity", "state_class": "measurement"},
    "°C": {"device_class": "temperature", "state_class": "measurement"},
    "°F": {"device_class": "temperature", "state_class": "measurement"},
    "K": {"device_class": "temperature", "state_class": "measurement"},
    "Pa": {"device_class": "pressure", "state_class": "measurement"},
    "bar": {"device_class": "pressure", "state_class": "measurement"},
    "W": {"device_class": "power", "state_class": "measurement"},
    "kW": {"device_class": "power", "state_class": "measurement"},
    "A": {"device_class": "current", "state_class": "measurement"},
    "V": {"device_class": "voltage", "state_class": "measurement"},
}


def auto_detect_metadata(source_state, user_unit, user_device_class, user_state_class):
    unit = user_unit
    device_class = user_device_class
    state_class = user_state_class

    if source_state:
        source_unit = source_state.attributes.get("unit_of_measurement")
        source_device_class = source_state.attributes.get("device_class")
        name = (source_state.name or "").lower()

        # Unit
        if not unit:
            unit = source_unit

        # Device class
        if not device_class:
            if source_device_class:
                device_class = source_device_class
            elif unit in AUTO_MAPPINGS:
                device_class = AUTO_MAPPINGS[unit]["device_class"]

        # Heuristik for %
        if unit == "%" and not user_device_class:
            if "battery" in name:
                device_class = "battery"
            elif "humidity" in name:
                device_class = "humidity"

        # State class
        if not state_class:
            if unit in AUTO_MAPPINGS:
                state_class = AUTO_MAPPINGS[unit]["state_class"]
            else:
                state_class = "measurement"

    return unit, device_class, state_class


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([AnalogScalerSensor(hass, entry)])


class AnalogScalerSensor(SensorEntity):
    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._state = None

        # Kombinér data + options (så edit virker)
        data = {**entry.data, **entry.options}

        self._source = data[CONF_SOURCE]
        self._min_analog = data[CONF_MIN_ANALOG]
        self._max_analog = data[CONF_MAX_ANALOG]
        self._min_limit = data[CONF_MIN_LIMIT]
        self._max_limit = data[CONF_MAX_LIMIT]

        self._unit = data.get(CONF_UNIT)
        self._device_class = data.get(CONF_DEVICE_CLASS)
        self._state_class = data.get(CONF_STATE_CLASS)

        self._metadata_initialized = False

        self._attr_name = entry.title
        self._attr_unique_id = f"{entry.entry_id}_scaled"

    async def async_added_to_hass(self):
        @callback
        def state_listener(event):
            self._update_state()
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self._hass,
                [self._source],
                state_listener
            )
        )

        # Første update
        self._update_state()

    def _update_state(self):
        state = self._hass.states.get(self._source)

        if not state or state.state in ("unknown", "unavailable"):
            self._state = None
            return

        # Init metadata én gang
        if not self._metadata_initialized:
            self._unit, self._device_class, self._state_class = auto_detect_metadata(
                state,
                self._unit,
                self._device_class,
                self._state_class,
            )
            self._metadata_initialized = True

        try:
            current = float(state.state)

            if (self._max_analog - self._min_analog) == 0:
                self._state = self._min_limit
                return

            normalized = (current - self._min_analog) / (self._max_analog - self._min_analog)
            normalized = max(0.0, min(1.0, normalized))

            scaled = normalized * (self._max_limit - self._min_limit) + self._min_limit
            self._state = round(scaled, 2)

        except Exception:
            self._state = None

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def state(self):
        return self._state
