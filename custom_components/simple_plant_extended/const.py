"""Constants for simple_plant_extended."""

from logging import Logger, getLogger

from homeassistant.const import Platform

STORAGE_KEY = "simple_plant_extended_data"

LOGGER: Logger = getLogger(__package__)

DOMAIN = "simple_plant_extended"

CONF_NOTIFY_SERVICES = "notify_services"
CONF_NOTIFICATIONS_ENABLED = "notifications_enabled"
CONF_DND_START = "dnd_start"
CONF_DND_END = "dnd_end"
CONF_BROADCAST_ENABLED = "broadcast_enabled"
CONF_BROADCAST_SERVICES = "broadcast_services"
CONF_BROADCAST_TIME_1 = "broadcast_time_1"
CONF_BROADCAST_TIME_2 = "broadcast_time_2"

DEFAULT_NOTIFICATIONS_ENABLED = True
DEFAULT_DND_START = "09:00:00"
DEFAULT_DND_END = "22:00:00"
DEFAULT_BROADCAST_ENABLED = False
DEFAULT_BROADCAST_SERVICES = ["notify.google_assistant_sdk"]
DEFAULT_BROADCAST_TIME_1 = "10:00:00"
DEFAULT_BROADCAST_TIME_2 = "19:00:00"

STORAGE_DIR = "simple_plant_extended"

MANUFACTURER = "Simple Plant Extended"

HEALTH_OPTIONS = [
    "notset",
    "poor",
    "fair",
    "good",
    "verygood",
    "excellent",
]

FEED_OPTIONS = [
    "liquid",
    "sticks",
    "pebbles",
]

ENABLED_OPTIONS = [
    "notset",
    "on",
    "off",
]

ILLUMINATION_OPTIONS = [
    "notset",
    "sunny",
    "partly_sunny",
    "shade",
]

SIZE_OPTIONS = [
    "notset",
    "seedling",
    "small",
    "medium",
    "large",
    "xlarge",
]

LOCATION_OPTIONS = [
    "notset",
    "living_room",
    "bedroom",
    "kitchen",
    "bathroom",
    "office",
    "balcony",
    "patio",
    "greenhouse",
    "outdoor",
]

SOIL_TYPE_OPTIONS = [
    "notset",
    "standard_potting_mix",
    "cactus_succulent",
    "orchid_bark",
    "peat_based",
    "coco_coir",
    "perlite_mix",
    "leca_hydroponics",
]

IMAGES_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".svg": "image/svg+xml",
}


PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.DATE,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]
