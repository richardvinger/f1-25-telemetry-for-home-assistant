"""Sensors for F1 25 Telemetry."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, 
    ERS_MODE_MAP,
    FIA_FLAG_MAP,
    SAFETY_CAR_STATUS_MAP, 
    WEATHER_MAP,
    TRACK_MAP,
    TYRE_COMPOUND_MAP,
)
from .coordinator import F125Coordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up F1 25 sensors."""
    coordinator: F125Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        F125SpeedSensor(coordinator),
        F125GearSensor(coordinator),
        F125RPMSensor(coordinator),
        F125ThrottleSensor(coordinator),
        F125BrakeSensor(coordinator),
        F125LapSensor(coordinator),
        F125PositionSensor(coordinator),
        F125SafetyCarSensor(coordinator),
        F125TrackTempSensor(coordinator),
        F125WeatherSensor(coordinator),
        F125SessionStatusSensor(coordinator),
        F125StartLightsSensor(coordinator),
        F125FlagSensor(coordinator),
        F125ERSStoreSensor(coordinator),
        F125ERSModeSensor(coordinator),
        F125DRSSensor(coordinator),
        F125DRSAllowedSensor(coordinator),
        F125TrackSensor(coordinator),
        F125TyreCompoundSensor(coordinator),
        F125TyreAgeSensor(coordinator),
        F125FuelLapsSensor(coordinator),
        F125LeaderSensor(coordinator),
        F125FastestLapSensor(coordinator),
        F125FastestLapTimeSensor(coordinator),
        F125LastLapTimeSensor(coordinator),
        F125LastLapSensor(coordinator),
        F125LapInvalidSensor(coordinator),
        F125DamageSensor(coordinator),
        F125TerminalDamageSensor(coordinator),
        F125RainChanceSensor(coordinator, 0, "Now"),
        F125RainChanceSensor(coordinator, 5, "in 5m"),
        F125RainChanceSensor(coordinator, 10, "in 10m"),
        F125RainChanceSensor(coordinator, 15, "in 15m"),
        
        # Damage booleans
        F125WingDamageSensor(coordinator, "Damaged Front Left Wing", "front_left_wing"),
        F125WingDamageSensor(coordinator, "Damaged Front Right Wing", "front_right_wing"),
        F125WingDamageSensor(coordinator, "Damaged Rear Wing", "rear_wing"),
        F125WingDamageSensor(coordinator, "Damaged Floor", "floor"),
    ]

    for i, label in enumerate(["Rear Left", "Rear Right", "Front Left", "Front Right"]):
        entities.append(F125TyreWearSensor(coordinator, i, label))
        entities.append(F125TyreTempSensor(coordinator, i, label))

    async_add_entities(entities)


class F1Sensor(CoordinatorEntity, SensorEntity):
    """Base class for F1 25 sensors."""

    def __init__(self, coordinator: F125Coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="F1 25 Game",
            manufacturer="Electronic Arts",
            model="F1 25 Telemetry",
            sw_version="2025.1.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # The coordinator manages availability based on last packet success
        return super().available

class F125SpeedSensor(F1Sensor):
    """Speed Sensor."""
    
    _attr_translation_key = "speed"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_name = "Speed"
    _attr_unique_id = "f1_25_speed"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["car_telemetry"].get("speed")
        return int(val) if val is not None else None

class F125GearSensor(F1Sensor):
    """Gear Sensor."""

    _attr_translation_key = "gear"
    _attr_name = "Gear"
    _attr_unique_id = "f1_25_gear"
    _attr_icon = "mdi:car-shift-pattern"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["car_telemetry"].get("gear")
        return int(val) if val is not None else None

class F125RPMSensor(F1Sensor):
    """RPM Sensor."""

    _attr_translation_key = "rpm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_name = "Engine RPM"
    _attr_unique_id = "f1_25_rpm"
    _attr_icon = "mdi:gauge"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["car_telemetry"].get("engine_rpm")
        return int(val) if val is not None else None

class F125ThrottleSensor(F1Sensor):
    """Throttle Sensor."""
    
    _attr_name = "Throttle"
    _attr_unique_id = "f1_25_throttle"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gas-station" # mdi:pedal not available usually
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        val = self.coordinator.data["car_telemetry"].get("throttle")
        if val is not None:
            return int(val * 100)
        return None

class F125BrakeSensor(F1Sensor):
    """Brake Sensor."""

    _attr_name = "Brake"
    _attr_unique_id = "f1_25_brake"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:alert-octagon-outline"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        val = self.coordinator.data["car_telemetry"].get("brake")
        if val is not None:
            return int(val * 100)
        return None

class F125LapSensor(F1Sensor):
    """Lap Number Sensor."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "laps"
    _attr_name = "Lap"
    _attr_unique_id = "f1_25_lap"
    _attr_icon = "mdi:flag-checkered"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["lap_data"].get("current_lap_num")
        return int(val) if val is not None else None

class F125PositionSensor(F1Sensor):
    """Position Sensor."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "pos"
    _attr_name = "Position"
    _attr_unique_id = "f1_25_position"
    _attr_icon = "mdi:podium"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["lap_data"].get("car_position")
        return int(val) if val is not None else None

class F125SafetyCarSensor(F1Sensor):
    """Safety Car Status Sensor."""

    _attr_name = "Safety Car"
    _attr_unique_id = "f1_25_safety_car"
    _attr_icon = "mdi:car-emergency"

    @property
    def native_value(self):
        status = self.coordinator.data["session"].get("safety_car_status")
        return SAFETY_CAR_STATUS_MAP.get(status, "Unknown")

class F125TrackTempSensor(F1Sensor):
    """Track Temperature Sensor."""

    _attr_name = "Track Temperature"
    _attr_unique_id = "f1_25_track_temp"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["session"].get("track_temperature")
        return int(val) if val is not None else None

class F125WeatherSensor(F1Sensor):
    """Weather Sensor."""

    _attr_name = "Weather"
    _attr_unique_id = "f1_25_weather"
    _attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self):
        w_id = self.coordinator.data["session"].get("weather")
        return WEATHER_MAP.get(w_id, "Unknown")

class F125SessionStatusSensor(F1Sensor):
    """Session Status Sensor."""
    _attr_name = "Session Status"
    _attr_unique_id = "f1_25_session_status"
    _attr_icon = "mdi:information-outline"

    @property
    def native_value(self):
        return self.coordinator.data["events"].get("session_status", "Unknown")

class F125StartLightsSensor(F1Sensor):
    """Start Lights Sensor."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "lights"
    _attr_name = "Start Lights"
    _attr_unique_id = "f1_25_start_lights"
    _attr_icon = "mdi:traffic-light"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["events"].get("start_lights", 0)
        return int(val) if val is not None else None

class F125FlagSensor(F1Sensor):
    """Flag Sensor."""
    _attr_name = "Flag"
    _attr_unique_id = "f1_25_flag"
    _attr_icon = "mdi:flag-variant"

    @property
    def native_value(self):
        flag = self.coordinator.data["car_status"].get("fia_flags")
        return FIA_FLAG_MAP.get(flag, "None")

class F125TyreWearSensor(F1Sensor):
    """Tyre Wear Sensor."""
    def __init__(self, coordinator, index, label):
        super().__init__(coordinator)
        self._index = index
        self._attr_name = f"Tyre Wear {label}"
        self._attr_unique_id = f"f1_25_tyre_wear_{label.lower().replace(' ', '_')}"
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:tire"

    @property
    def native_value(self):
        wear = self.coordinator.data["car_damage"].get("tyres_wear")
        if wear and len(wear) > self._index:
            return int(wear[self._index])
        return None

class F125TyreTempSensor(F1Sensor):
    """Tyre Temperature Sensor."""
    def __init__(self, coordinator, index, label):
        super().__init__(coordinator)
        self._index = index
        self._attr_name = f"Tyre Temp {label}"
        self._attr_unique_id = f"f1_25_tyre_temp_{label.lower().replace(' ', '_')}"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:thermometer-lines"

    @property
    def native_value(self):
        temps = self.coordinator.data["car_telemetry"].get("tyre_surface_temp")
        if temps and len(temps) > self._index:
            return temps[self._index]
        return None

class F125ERSStoreSensor(F1Sensor):
    """ERS Store Sensor (Percentage)."""
    _attr_name = "ERS Store"
    _attr_unique_id = "f1_25_ers_store"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:battery-flash"
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data["car_status"].get("ers_store")
        if val is not None:
            # 4,000,000 Joules is 100%
            pct = (val / 4000000.0) * 100.0
            return float(round(pct, 1))
        return None

class F125ERSModeSensor(F1Sensor):
    """ERS Mode Sensor."""
    _attr_name = "ERS Mode"
    _attr_unique_id = "f1_25_ers_mode"
    _attr_icon = "mdi:car-electric"

    @property
    def native_value(self):
        mode = self.coordinator.data["car_status"].get("ers_deploy_mode")
        return ERS_MODE_MAP.get(mode, "Unknown")

class F125DRSSensor(F1Sensor):
    """DRS State Sensor (On/Off)."""
    _attr_name = "DRS State"
    _attr_unique_id = "f1_25_drs_state"
    _attr_icon = "mdi:wing"

    @property
    def native_value(self):
        val = self.coordinator.data["car_telemetry"].get("drs")
        return "On" if val == 1 else "Off"

class F125DRSAllowedSensor(F1Sensor):
    """DRS Allowed Sensor."""
    _attr_name = "DRS Allowed"
    _attr_unique_id = "f1_25_drs_allowed"
    _attr_icon = "mdi:check-circle-outline"

    @property
    def native_value(self):
        val = self.coordinator.data["car_status"].get("drs_allowed")
        return "Allowed" if val == 1 else "Not Allowed"

# --- New Advanced Sensors ---

class F125TrackSensor(F1Sensor):
    """Track name sensor."""
    _attr_name = "Track"
    _attr_unique_id = "f1_25_track"
    _attr_icon = "mdi:map-marker-path"

    @property
    def native_value(self):
        val = self.coordinator.data["session"].get("track_id")
        return TRACK_MAP.get(val, "Unknown")

class F125TyreCompoundSensor(F1Sensor):
    """Tyre compound sensor."""
    _attr_name = "Tyre Compound"
    _attr_unique_id = "f1_25_tyre_compound"
    _attr_icon = "mdi:tire"

    @property
    def native_value(self):
        val = self.coordinator.data["car_status"].get("tyre_visual")
        return TYRE_COMPOUND_MAP.get(val, "Unknown")

class F125TyreAgeSensor(F1Sensor):
    """Tyre age sensor (laps)."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "laps"
    _attr_name = "Tyre Age"
    _attr_unique_id = "f1_25_tyre_age"
    _attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int | None:
        val = self.coordinator.data["car_status"].get("tyre_age")
        return int(val) if val is not None else None

class F125FuelLapsSensor(F1Sensor):
    """Fuel remaining in laps."""
    _attr_name = "Fuel Laps"
    _attr_unique_id = "f1_25_fuel_laps"
    _attr_icon = "mdi:fuel"

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data["car_status"].get("fuel_remaining_laps")
        return float(round(val, 2)) if val is not None else None

class F125LeaderSensor(F1Sensor):
    """Leader name sensor."""
    _attr_name = "Leader"
    _attr_unique_id = "f1_25_leader"
    _attr_icon = "mdi:account-star"

    @property
    def native_value(self):
        idx = self.coordinator.data["session"].get("leader_index")
        if idx is not None:
            return self.coordinator.data["participants"].get(idx, "Unknown")
        return "Unknown"

class F125FastestLapSensor(F1Sensor):
    """Fastest lap driver sensor."""
    _attr_name = "Fastest Lap"
    _attr_unique_id = "f1_25_fastest_lap"
    _attr_icon = "mdi:timer-star"

    @property
    def native_value(self):
        idx = self.coordinator.data["fastest_lap"].get("car_index")
        if idx is not None and idx != 255:
            return self.coordinator.data["participants"].get(idx, "Unknown")
        return "None"

class F125FastestLapTimeSensor(F1Sensor):
    """Fastest lap time sensor."""
    _attr_name = "Fastest Lap Time"
    _attr_unique_id = "f1_25_fastest_lap_time"
    _attr_icon = "mdi:timer-outline"

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data["fastest_lap"].get("lap_time")
        return float(round(val, 3)) if val and val > 0 else None

class F125LastLapTimeSensor(F1Sensor):
    """Last lap time sensor."""
    _attr_name = "Last Lap Time"
    _attr_unique_id = "f1_25_last_lap_time"
    _attr_icon = "mdi:history"

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data["lap_data"].get("last_lap_time")
        return float(val / 1000.0) if val and val > 0 else None

class F125LastLapSensor(F1Sensor):
    """Last lap driver sensor (String)."""
    _attr_name = "Last Lap"
    _attr_unique_id = "f1_25_last_lap"
    _attr_icon = "mdi:timer-sand"

    @property
    def native_value(self):
        """Return formatted time."""
        return self.coordinator.data["lap_data"].get("last_lap_str", "0:00.000")

class F125LapInvalidSensor(F1Sensor):
    """Lap invalid sensor."""
    _attr_name = "Lap Invalid"
    _attr_unique_id = "f1_25_lap_invalid"
    _attr_icon = "mdi:alert-circle"

    @property
    def native_value(self):
        val = self.coordinator.data["lap_data"].get("current_lap_invalid")
        return "Yes" if val == 1 else "No"

class F125DamageSensor(F1Sensor):
    """General damage sensor."""
    _attr_name = "Damage"
    _attr_unique_id = "f1_25_damage"
    _attr_icon = "mdi:car-wrench"

    @property
    def native_value(self):
        val = self.coordinator.data["car_damage"].get("has_damage")
        return "Yes" if val == 1 else "No"

class F125TerminalDamageSensor(F1Sensor):
    """Terminal damage sensor."""
    _attr_name = "Terminal Damage"
    _attr_unique_id = "f1_25_terminal_damage"
    _attr_icon = "mdi:car-crash"

    @property
    def native_value(self):
        val = self.coordinator.data["car_damage"].get("terminal")
        return "Yes" if val == 1 else "No"

class F125RainChanceSensor(F1Sensor):
    """Rain chance sensor."""
    def __init__(self, coordinator, minutes, name_suffix):
        super().__init__(coordinator)
        self._minutes = minutes
        self._attr_name = f"Rain Chance {name_suffix}"
        self._attr_unique_id = f"f1_25_rain_chance_{minutes}"
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:weather-rainy"

    @property
    def native_value(self) -> int:
        forecast = self.coordinator.data.get("forecast", [])
        for f in forecast:
            if f["time"] == self._minutes:
                return int(f["rain"])
        return 0

class F125WingDamageSensor(F1Sensor):
    """Wing damage boolean sensor."""
    def __init__(self, coordinator, label, key):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = label
        self._attr_unique_id = f"f1_25_damage_{key}"
        self._attr_icon = "mdi:car-back"

    @property
    def native_value(self):
        val = self.coordinator.data.get("car_damage", {}).get(self._key, 0)
        return "Yes" if val > 0 else "No"
