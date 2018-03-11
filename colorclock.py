import asyncio
import logging
import colorsys
import datetime

import voluptuous as vol

from homeassistant.components.scene import Scene
from homeassistant.const import CONF_PLATFORM
import homeassistant.helpers.config_validation as cv
import homeassistant.components.light as light

_LOGGER = logging.getLogger(__name__)

CONF_HOUR_LIGHT = 'hour_light'
CONF_MINUTE_LIGHT = 'minute_light'
CONF_SECOND_LIGHT = 'second_light'
CONF_24H_MODE = '24h_mode'
CONF_CCW = 'ccw'
CONF_ANGLE_OFFSET = 'angle_offset'

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): 'colorclock',
    vol.Optional(CONF_HOUR_LIGHT): cv.entity_id,
    vol.Optional(CONF_MINUTE_LIGHT): cv.entity_id,
    vol.Optional(CONF_SECOND_LIGHT): cv.entity_id,
    vol.Optional(CONF_24H_MODE): cv.boolean,
    vol.Optional(CONF_CCW): cv.boolean,
    vol.Optional(CONF_ANGLE_OFFSET): vol.All(vol.Coerce(int), vol.Range(min=0, max=359)),
})

# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    hour_light_id = config.get(CONF_HOUR_LIGHT, None)
    minute_light_id = config.get(CONF_MINUTE_LIGHT, None)
    second_light_id = config.get(CONF_SECOND_LIGHT, None)
    twentyfour_mode = config.get(CONF_24H_MODE, False)
    ccw = config.get(CONF_CCW, False)
    angle_offset = config.get(CONF_ANGLE_OFFSET, 0)

    scene = ColorClockScene(hass, hour_light_id, minute_light_id, second_light_id,
                            twentyfour_mode, ccw, angle_offset)
    async_add_devices([scene])
    return True

class ColorClockScene(Scene):
    def __init__(self, hass, hour_light_id, minute_light_id, second_light_id, twentyfour_mode, ccw, angle_offset):
        self.hass = hass
        self._hour_light_id = hour_light_id
        self._minute_light_id = minute_light_id
        self._second_light_id = second_light_id
        self._twentyfour_mode = twentyfour_mode
        self._ccw = ccw
        self._angle_offset = angle_offset

    @property
    def name(self):
        return "Color Clock"

    def set_light(self, entity_id, value):
        if not light.is_on(self.hass, entity_id):
            return

        if self._ccw:
            value = 1 - value

        value = (value + (self._angle_offset / 360)) % 1
        rgb = tuple(int(i * 255) for i in colorsys.hsv_to_rgb(value, 1, 1))
        logging.debug("Setting light %s to %s, value=%.2f", entity_id, rgb, value)
        light.turn_on(self.hass, entity_id=entity_id, rgb_color=rgb)

    @asyncio.coroutine
    def async_activate(self):
        now = datetime.datetime.now()
        # seconds since midnight
        ssm = (now.hour * 3600) + (now.minute * 60) + now.second

        if self._hour_light_id is not None:
            if self._twentyfour_mode:
                value = ssm / (24 * 3600)
            else:
                value = (ssm / (12 * 3600)) % 1

            self.set_light(self._hour_light_id, value)

        if self._minute_light_id is not None:
            value = (ssm / 3600) % 1
            self.set_light(self._minute_light_id, value)

        if self._second_light_id is not None:
            value = (ssm / 60) % 1
            self.set_light(self._second_light_id, value)

