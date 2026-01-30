"""Runtime notifications and broadcast manager for Simple Plant Extended."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BROADCAST_ENABLED,
    CONF_BROADCAST_SERVICES,
    CONF_BROADCAST_TIME_1,
    CONF_BROADCAST_TIME_2,
    CONF_DND_END,
    CONF_DND_START,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFY_SERVICES,
    DEFAULT_BROADCAST_ENABLED,
    DEFAULT_BROADCAST_SERVICES,
    DEFAULT_BROADCAST_TIME_1,
    DEFAULT_BROADCAST_TIME_2,
    DEFAULT_DND_END,
    DEFAULT_DND_START,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DOMAIN,
)


class NotificationManager:
    """Manage runtime notifications and broadcast schedules."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the notification manager."""
        self.hass = hass
        self._unsub_state: Any | None = None
        self._unsub_broadcast: list[Any] = []
        self._unsub_action: Any | None = None
        self._translations: dict[str, Any] | None = None
        self._translations_lang: str | None = None

    async def async_start(self) -> None:
        """Start listeners."""
        await self.async_refresh()
        if self._unsub_action is None:
            self._unsub_action = self.hass.bus.async_listen(
                "mobile_app_notification_action", self._handle_mobile_action
            )

    async def async_stop(self) -> None:
        """Stop listeners."""
        if self._unsub_state is not None:
            self._unsub_state()
            self._unsub_state = None
        for unsub in self._unsub_broadcast:
            unsub()
        self._unsub_broadcast = []
        if self._unsub_action is not None:
            self._unsub_action()
            self._unsub_action = None

    async def async_refresh(self) -> None:
        """Refresh listeners and schedules based on current options and plants."""
        # Refresh state listeners
        if self._unsub_state is not None:
            self._unsub_state()
            self._unsub_state = None

        entity_ids = self._get_notification_entity_ids()
        if entity_ids:
            self._unsub_state = async_track_state_change_event(
                self.hass, entity_ids, self._handle_state_change
            )

        # Refresh broadcast schedules
        for unsub in self._unsub_broadcast:
            unsub()
        self._unsub_broadcast = []

        options = self._get_options()
        if options[CONF_BROADCAST_ENABLED]:
            for time_value in (
                options[CONF_BROADCAST_TIME_1],
                options[CONF_BROADCAST_TIME_2],
            ):
                parsed = dt_util.parse_time(time_value)
                if parsed is None:
                    continue
                unsub = async_track_time_change(
                    self.hass,
                    self._handle_broadcast_time,
                    hour=parsed.hour,
                    minute=parsed.minute,
                    second=parsed.second,
                )
                self._unsub_broadcast.append(unsub)

    def _get_options(self) -> dict[str, Any]:
        entries = self.hass.config_entries.async_entries(DOMAIN)
        options = entries[0].options if entries else {}
        return {
            CONF_NOTIFY_SERVICES: options.get(CONF_NOTIFY_SERVICES, []),
            CONF_NOTIFICATIONS_ENABLED: options.get(
                CONF_NOTIFICATIONS_ENABLED, DEFAULT_NOTIFICATIONS_ENABLED
            ),
            CONF_DND_START: options.get(CONF_DND_START, DEFAULT_DND_START),
            CONF_DND_END: options.get(CONF_DND_END, DEFAULT_DND_END),
            CONF_BROADCAST_ENABLED: options.get(
                CONF_BROADCAST_ENABLED, DEFAULT_BROADCAST_ENABLED
            ),
            CONF_BROADCAST_SERVICES: options.get(
                CONF_BROADCAST_SERVICES, DEFAULT_BROADCAST_SERVICES
            ),
            CONF_BROADCAST_TIME_1: options.get(
                CONF_BROADCAST_TIME_1, DEFAULT_BROADCAST_TIME_1
            ),
            CONF_BROADCAST_TIME_2: options.get(
                CONF_BROADCAST_TIME_2, DEFAULT_BROADCAST_TIME_2
            ),
        }

    def _get_plant_slugs(self) -> list[str]:
        plants: list[str] = []
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            plant_name = entry.data.get("name", entry.title).lower().replace(" ", "_")
            plants.append(plant_name)
        return sorted(set(plants))

    def _get_notification_entity_ids(self) -> list[str]:
        entity_ids: list[str] = []
        for plant in self._get_plant_slugs():
            entity_ids.extend(
                [
                    f"binary_sensor.simple_plant_extended_todo_{plant}",
                    f"binary_sensor.simple_plant_extended_problem_{plant}",
                    f"binary_sensor.simple_plant_extended_fertilization_todo_{plant}",
                    f"binary_sensor.simple_plant_extended_misting_todo_{plant}",
                    f"binary_sensor.simple_plant_extended_cleaning_todo_{plant}",
                ]
            )
        return entity_ids

    async def _get_translations(self) -> dict[str, Any]:
        lang = self.hass.config.language
        if self._translations is None or self._translations_lang != lang:
            self._translations = self._load_translation_file(lang)
            self._translations_lang = lang
        return self._translations

    async def _t(self, key: str, **kwargs: Any) -> str:
        translations = await self._get_translations()
        template = self._get_nested_translation(translations, key) or key
        try:
            return template.format(**kwargs)
        except Exception:  # noqa: BLE001
            return template

    def _load_translation_file(self, lang: str) -> dict[str, Any]:
        translations_dir = Path(__file__).parent / "translations"

        def load(lang_code: str) -> dict[str, Any]:
            path = translations_dir / f"{lang_code}.json"
            if not path.exists():
                return {}
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                return {}

        data = load(lang)
        if not data and "-" in lang:
            data = load(lang.split("-", 1)[0])
        if not data:
            data = load("en")
        return data

    def _get_nested_translation(self, data: dict[str, Any], key: str) -> str | None:
        value: Any = data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value if isinstance(value, str) else None

    def _within_dnd_window(self, start: str, end: str) -> bool:
        now = dt_util.now().time()
        start_time = dt_util.parse_time(start)
        end_time = dt_util.parse_time(end)
        if start_time is None or end_time is None:
            return True
        if start_time <= end_time:
            return start_time <= now <= end_time
        # Overnight window
        return now >= start_time or now <= end_time

    def _plant_display_name(self, plant: str) -> str:
        return plant.replace("_", " ").capitalize()

    @callback
    def _handle_state_change(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != "on":
            return

        options = self._get_options()
        if not options[CONF_NOTIFICATIONS_ENABLED]:
            return
        if not self._within_dnd_window(options[CONF_DND_START], options[CONF_DND_END]):
            return

        entity_id: str = new_state.entity_id
        plant = entity_id.split("_")[-1]
        plant_name = self._plant_display_name(plant)

        # Map entity ID patterns to task types
        task_mapping = {
            "binary_sensor.simple_plant_extended_todo_": ("water", "today"),
            "binary_sensor.simple_plant_extended_problem_": ("water", "late"),
            "binary_sensor.simple_plant_extended_fertilization_todo_": (
                "fertilize",
                "today",
            ),
            "binary_sensor.simple_plant_extended_misting_todo_": ("mist", "today"),
            "binary_sensor.simple_plant_extended_cleaning_todo_": ("clean", "today"),
        }

        for prefix, (task, status) in task_mapping.items():
            if entity_id.startswith(prefix):
                self.hass.async_create_task(
                    self._send_task_notification(task, status, plant, plant_name)
                )
                break

    async def _send_task_notification(
        self, task: str, status: str, plant: str, plant_name: str
    ) -> None:
        options = self._get_options()
        services = options[CONF_NOTIFY_SERVICES] or ["notify.notify"]

        title_key = (
            f"component.simple_plant_extended.notification.{task}_{status}_title"
        )
        message_key = f"component.simple_plant_extended.notification.{task}_message"

        title_kwargs: dict[str, Any] = {"plant": plant_name}
        if task == "water" and status == "late":
            days = self._water_overdue_days(plant)
            title_kwargs["days"] = days

        title = await self._t(title_key, **title_kwargs)
        message = await self._t(message_key, plant=plant_name)

        action_prefix = task.upper()
        action = f"{action_prefix}_{plant}"
        actions = [
            {
                "action": action,
                "title": await self._t(
                    "component.simple_plant_extended.notification.action_mark_done"
                ),
            },
            {
                "action": f"{action}_skip",
                "title": await self._t(
                    "component.simple_plant_extended.notification.action_skip"
                ),
            },
        ]

        for service in services:
            await self._call_notify_service(
                service,
                {
                    "title": title,
                    "message": message,
                    "data": {"actions": actions, "tag": plant},
                },
            )

    def _water_overdue_days(self, plant: str) -> int:
        entity_id = f"sensor.simple_plant_extended_next_watering_{plant}"
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return 0
        next_date = dt_util.parse_datetime(state.state) or dt_util.parse_date(
            state.state
        )
        if next_date is None:
            return 0
        next_dt = dt_util.as_datetime(next_date)
        return max((dt_util.now() - next_dt).days, 0)

    async def _call_notify_service(self, service: str, data: dict[str, Any]) -> None:
        if "." in service:
            domain, service_name = service.split(".", 1)
        else:
            domain, service_name = "notify", service
        await self.hass.services.async_call(domain, service_name, data, blocking=False)

    @callback
    def _handle_mobile_action(self, event: Event) -> None:
        action = event.data.get("action")
        if not action or action.endswith("_skip"):
            return

        if "_" not in action:
            return

        action_type, plant = action.split("_", 1)
        action_type = action_type.lower()

        button_map = {
            "water": "button.simple_plant_extended_mark_watered_{}",
            "fertilize": "button.simple_plant_extended_mark_fertilized_{}",
            "mist": "button.simple_plant_extended_mark_misted_{}",
            "clean": "button.simple_plant_extended_mark_cleaned_{}",
        }

        if action_type not in button_map:
            return

        entity_id = button_map[action_type].format(plant)
        self.hass.async_create_task(
            self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": entity_id},
                blocking=False,
            )
        )

    @callback
    def _handle_broadcast_time(self, _now: datetime) -> None:
        self.hass.async_create_task(self._send_broadcast())

    async def _send_broadcast(self) -> None:
        options = self._get_options()
        if not options[CONF_BROADCAST_ENABLED]:
            return

        services = options[CONF_BROADCAST_SERVICES] or ["notify.google_assistant_sdk"]
        message = await self._build_broadcast_message()

        for service in services:
            await self._call_notify_service(service, {"message": message})

    async def _collect_watering_tasks(self, today: str) -> list[str]:
        """Collect watering tasks for broadcast."""
        items: list[str] = []

        for state in self.hass.states.async_all("sensor"):
            if not state.entity_id.startswith(
                "sensor.simple_plant_extended_next_watering_"
            ):
                continue
            plant = state.entity_id.split("_")[-1]
            plant_name = self._plant_display_name(plant)
            last_entity_id = f"date.simple_plant_extended_last_watered_{plant}"
            next_date = state.state
            last_date = self.hass.states.get(last_entity_id)
            overdue_entity = f"binary_sensor.simple_plant_extended_problem_{plant}"

            if self.hass.states.is_state(overdue_entity, "on"):
                next_dt = dt_util.parse_datetime(next_date) or dt_util.parse_date(
                    next_date
                )
                when = (
                    dt_util.relative_time(dt_util.as_datetime(next_dt))
                    if next_dt
                    else ""
                )
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.water_overdue",
                        plant=plant_name,
                        when=when,
                    )
                )
            if today in next_date and (
                last_date is None or today not in last_date.state
            ):
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.water_today",
                        plant=plant_name,
                    )
                )

        return items

    async def _collect_fertilization_tasks(self, today: str) -> list[str]:
        """Collect fertilization tasks for broadcast."""
        items: list[str] = []

        for state in self.hass.states.async_all("sensor"):
            if not state.entity_id.startswith(
                "sensor.simple_plant_extended_next_fertilization_"
            ):
                continue
            plant = state.entity_id.split("_")[-1]
            plant_name = self._plant_display_name(plant)
            last_entity_id = f"date.simple_plant_extended_last_fertilized_{plant}"
            feed_type = self.hass.states.get(
                f"select.simple_plant_extended_feed_method_{plant}"
            )
            next_date = state.state
            last_date = self.hass.states.get(last_entity_id)

            next_dt = dt_util.parse_datetime(next_date) or dt_util.parse_date(next_date)
            if next_dt and dt_util.as_datetime(next_dt) < (
                dt_util.now() - timedelta(days=1)
            ):
                when = dt_util.relative_time(dt_util.as_datetime(next_dt))
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.fertilize_overdue",
                        plant=plant_name,
                        feed_type=feed_type.state if feed_type else "",
                        when=when,
                    )
                )

            if today in next_date and (
                last_date is None or today not in last_date.state
            ):
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.fertilize_today",
                        plant=plant_name,
                        feed_type=feed_type.state if feed_type else "",
                    )
                )

        return items

    async def _collect_misting_tasks(self) -> list[str]:
        """Collect misting tasks for broadcast."""
        items: list[str] = []

        for state in self.hass.states.async_all("binary_sensor"):
            if not state.entity_id.startswith(
                "binary_sensor.simple_plant_extended_misting_todo_"
            ):
                continue
            plant = state.entity_id.split("_")[-1]
            plant_name = self._plant_display_name(plant)
            enabled = self.hass.states.is_state(
                f"select.simple_plant_extended_misting_enabled_{plant}", "on"
            )
            late = self.hass.states.is_state(
                f"binary_sensor.simple_plant_extended_misting_problem_{plant}", "on"
            )
            next_state = self.hass.states.get(
                f"sensor.simple_plant_extended_next_misting_{plant}"
            )

            if enabled and late and next_state is not None:
                next_dt = dt_util.parse_datetime(
                    next_state.state
                ) or dt_util.parse_date(next_state.state)
                when = (
                    dt_util.relative_time(dt_util.as_datetime(next_dt))
                    if next_dt
                    else ""
                )
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.mist_overdue",
                        plant=plant_name,
                        when=when,
                    )
                )
            if enabled and state.state == "on":
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.mist_today",
                        plant=plant_name,
                    )
                )

        return items

    async def _collect_cleaning_tasks(self) -> list[str]:
        """Collect cleaning tasks for broadcast."""
        items: list[str] = []

        for state in self.hass.states.async_all("binary_sensor"):
            if not state.entity_id.startswith(
                "binary_sensor.simple_plant_extended_cleaning_todo_"
            ):
                continue
            plant = state.entity_id.split("_")[-1]
            plant_name = self._plant_display_name(plant)
            enabled = self.hass.states.is_state(
                f"select.simple_plant_extended_cleaning_enabled_{plant}", "on"
            )
            late = self.hass.states.is_state(
                f"binary_sensor.simple_plant_extended_cleaning_problem_{plant}", "on"
            )
            next_state = self.hass.states.get(
                f"sensor.simple_plant_extended_next_cleaning_{plant}"
            )

            if enabled and late and next_state is not None:
                next_dt = dt_util.parse_datetime(
                    next_state.state
                ) or dt_util.parse_date(next_state.state)
                when = (
                    dt_util.relative_time(dt_util.as_datetime(next_dt))
                    if next_dt
                    else ""
                )
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.clean_overdue",
                        plant=plant_name,
                        when=when,
                    )
                )
            if enabled and state.state == "on":
                items.append(
                    await self._t(
                        "component.simple_plant_extended.broadcast.clean_today",
                        plant=plant_name,
                    )
                )

        return items

    async def _build_broadcast_message(self) -> str:
        today = dt_util.now().strftime("%Y-%m-%d")

        # Collect all tasks
        items = (
            await self._collect_watering_tasks(today)
            + await self._collect_fertilization_tasks(today)
            + await self._collect_misting_tasks()
            + await self._collect_cleaning_tasks()
        )

        if not items:
            return await self._t("component.simple_plant_extended.broadcast.no_tasks")

        return " ".join(items)
