"""Data Coordinator for F1 25 Telemetry."""
import asyncio
import logging
import socket
import struct
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    CONF_PORT,
    CONF_FORWARD_ENABLED,
    CONF_FORWARD_IP,
    CONF_FORWARD_PORT,
    DEVICE_ID,
    PACKET_HEADER_SIZE,
    PACKET_ID_CAR_DAMAGE,
    PACKET_ID_CAR_STATUS,
    PACKET_ID_CAR_TELEMETRY,
    PACKET_ID_EVENT,
    PACKET_ID_LAP_DATA,
    PACKET_ID_PARTICIPANTS,
    PACKET_ID_SESSION,
    PACKET_SIZES,
)

_LOGGER = logging.getLogger(__name__)

RELEVANT_PACKETS = [
    PACKET_ID_SESSION,
    PACKET_ID_LAP_DATA,
    PACKET_ID_CAR_TELEMETRY,
    PACKET_ID_CAR_STATUS,
    PACKET_ID_CAR_DAMAGE,
    PACKET_ID_EVENT,
    PACKET_ID_PARTICIPANTS,
]

class F125Coordinator(DataUpdateCoordinator):
    """Class to manage fetching F1 25 data via UDP."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )
        self.entry = entry
        # Priority: Options > Data > DEFAULT
        self.port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
        self.transport = None
        self.protocol = None
        self._last_update = 0 # Track last notification time
        self._forward_socket = None
        self._forward_dest = None
        
        # Check forwarding
        forward_enabled = entry.options.get(CONF_FORWARD_ENABLED, entry.data.get(CONF_FORWARD_ENABLED, False))
        if forward_enabled:
            ip = entry.options.get(CONF_FORWARD_IP, entry.data.get(CONF_FORWARD_IP))
            port = entry.options.get(CONF_FORWARD_PORT, entry.data.get(CONF_FORWARD_PORT, DEFAULT_PORT))
            if ip and port:
                self._forward_dest = (ip, port)
                self._forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                _LOGGER.info(f"UDP Forwarding enabled to {ip}:{port}")
        
        # Storage for the latest packet of each type
        self.data = {
            "session": {},
            "lap_data": {},
            "car_telemetry": {},
            "car_status": {},
            "car_damage": {},
            "participants": {}, # car_index -> name
            "fastest_lap": {
                "car_index": 255,
                "lap_time": 0.0,
            },
            "events": {
                "start_lights": 0,
                "session_status": "Unknown",
            },
            "forecast": [], # List of rain percentages
        }

    async def async_start(self):
        """Start UDP listener."""
        _LOGGER.debug(f"Starting UDP listener on port {self.port}")
        loop = asyncio.get_running_loop()
        
        try:
            # Create UDP endpoint
            self.transport, self.protocol = await loop.create_datagram_endpoint(
                lambda: F125Protocol(self.process_packet),
                local_addr=("0.0.0.0", self.port)
            )
        except Exception as e:
            _LOGGER.error(f"Failed to start UDP listener: {e}")

    @callback
    def async_stop(self):
        """Stop UDP listener."""
        if self.transport:
            self.transport.close()
            self.transport = None
        if self._forward_socket:
            self._forward_socket.close()
            self._forward_socket = None

    @callback
    def async_update_options(self):
        """Update options."""
        # Refresh forwarding
        if self._forward_socket:
            self._forward_socket.close()
            self._forward_socket = None
        self._forward_dest = None

        forward_enabled = self.entry.options.get(CONF_FORWARD_ENABLED, self.entry.data.get(CONF_FORWARD_ENABLED, False))
        if forward_enabled:
            ip = self.entry.options.get(CONF_FORWARD_IP, self.entry.data.get(CONF_FORWARD_IP))
            port = self.entry.options.get(CONF_FORWARD_PORT, self.entry.data.get(CONF_FORWARD_PORT, DEFAULT_PORT))
            if ip and port:
                self._forward_dest = (ip, port)
                self._forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                _LOGGER.info(f"UDP Forwarding enabled to {ip}:{port}")

    @callback
    def process_packet(self, data: bytes):
        """Process incoming UDP packet."""
        if len(data) < PACKET_HEADER_SIZE:
            return

        # Parse Header
        header_fmt = "<HBBBBBQfIIBB"
        try:
            (
                packet_format,
                game_year,
                game_major_version,
                game_minor_version,
                packet_version,
                packet_id,
                session_uid,
                session_time,
                frame_identifier,
                overall_frame_identifier,
                player_car_index,
                secondary_player_car_index,
            ) = struct.unpack(header_fmt, data[:PACKET_HEADER_SIZE])
        except struct.error:
            return

        # Sanity check packet size
        # Check against mapped size if we know it
        expected_size = PACKET_SIZES.get(packet_id)
        if expected_size and len(data) != expected_size:
            _LOGGER.debug(f"Packet size mismatch for ID {packet_id}: expected {expected_size}, got {len(data)}")
            return

        payload = data[PACKET_HEADER_SIZE:]
        
        # Verbose debug log
        if packet_id in RELEVANT_PACKETS:
             _LOGGER.debug(f"Received relevant packet ID {packet_id} for car {player_car_index}")

        # Forward if enabled
        if self._forward_socket and self._forward_dest:
            try:
                self._forward_socket.sendto(data, self._forward_dest) # Forward the full packet, not just payload
            except Exception as e:
                _LOGGER.error(f"Failed to forward UDP packet: {e}")

        if packet_id == PACKET_ID_SESSION:
            self.parse_session_packet(payload)
        elif packet_id == PACKET_ID_LAP_DATA:
            self.parse_lap_data_packet(payload, player_car_index)
        elif packet_id == PACKET_ID_CAR_TELEMETRY:
            self.parse_car_telemetry_packet(payload, player_car_index)
        elif packet_id == PACKET_ID_CAR_STATUS:
            self.parse_car_status_packet(payload, player_car_index)
        elif packet_id == PACKET_ID_CAR_DAMAGE:
            self.parse_car_damage_packet(payload, player_car_index)
        elif packet_id == PACKET_ID_PARTICIPANTS:
            self.parse_participants_packet(payload)
        elif packet_id == PACKET_ID_EVENT:
            self.parse_event_packet(payload)
        
        if packet_id in RELEVANT_PACKETS:
            # Throttle high-frequency updates (Telemetry and Lap Data) to 10Hz
            if packet_id in [PACKET_ID_CAR_TELEMETRY, PACKET_ID_LAP_DATA]:
                now = time.monotonic()
                if now - self._last_update < 0.1:
                    return
                self._last_update = now

            self.async_set_updated_data(self.data)

    def parse_session_packet(self, payload: bytes):
        """Parse session packet."""
        # Derived from struct PacketSessionData
        # offsets:
        # header (29)
        # m_weather (uint8)
        # m_trackTemperature (int8)
        # m_airTemperature (int8)
        # m_totalLaps (uint8)
        # m_trackLength (uint16)
        # m_sessionType (uint8)
        # m_trackId (int8)
        # ...
        try:
            # We unpack just the beginning of the struct as we don't need everything yet
            # weather (B), trackTemp(b), airTemp(b), totalLaps(B), trackLength(H), sessionType(B), trackId(b)
            # timeleft(H), duration(H), pitLimit(B), gamePaused(B), isSpectating(B), specIndex(B), sliPro(B), numMarshal(B)
            # marshalZones(21 * 5 bytes) ...
            
            # Let's just grab the scalar start part.
            # B b b B H B b B H H B B B B B B (size 19 bytes)
            fmt = "<BbbBHBbBHHBBBBBB" 
            # This covers up to numMarshalZones.
            
            unpacked = struct.unpack(fmt, payload[:19])
            
            session_type_id = unpacked[5]
            session_status = self.data["events"].get("session_status", "Inactive")
            
            # Improve session status logic
            # If session time left is valid and session type is not unknown, it's "Active"
            # unless an event says otherwise.
            if session_type_id != 0 and unpacked[8] > 0:
                if session_status in ["Unknown", "Inactive"]:
                    session_status = "Active"
            elif session_status == "Active":
                session_status = "Ended"

            self.data["session"] = {
                "weather": unpacked[0],
                "track_temperature": unpacked[1],
                "air_temperature": unpacked[2],
                "total_laps": unpacked[3],
                "track_length": unpacked[4],
                "session_type": session_type_id,
                "track_id": unpacked[6],
                "session_time_left": unpacked[8],
                "safety_car_status": 0,
            }
            # Remove "game_paused" tracking as requested
            self.data["events"]["session_status"] = session_status
            
            # Marshal zones: 21 * 5 = 105 bytes. Starts at offset 19.
            # Base data is 19 bytes.
            # Safety car status is after marshal zones: 19 + 105 = 124.
            # Network game is 125.
            # Num weather samples is 126.
            # Forecast samples start at 127.
            if len(payload) > 124:
                self.data["session"]["safety_car_status"] = payload[124]
            
            if len(payload) > 126:
                num_samples = payload[126]
                samples = []
                # WeatherForecastSample is 8 bytes. Rain pct is at offset 7.
                for i in range(num_samples):
                    s_offset = 127 + (i * 8)
                    if s_offset + 8 <= len(payload):
                        rain_pct = payload[s_offset + 7]
                        time_offset = payload[s_offset + 1]
                        samples.append({"time": time_offset, "rain": rain_pct})
                self.data["forecast"] = samples
            
            # Quick hack to get safety car status:
            # It's after marshal zones.
            # MarshalZone = 5 bytes. 21 of them = 105 bytes.
            # Offset = 19 + 105 = 124.
            # m_safetyCarStatus is next byte (uint8)
            safety_car_status = payload[124]
            self.data["session"]["safety_car_status"] = safety_car_status
            
        except struct.error:
            pass

    def parse_lap_data_packet(self, payload: bytes, player_index: int):
        """Parse lap data packet."""
        # Car Lap Data size = 60 bytes (approx, need to calc specific struct size)
        # struct LapData { ... }
        # Let's see struct size.
        # uint32 lastLapTime (4)
        # uint32 currentLapTime (4)
        # uint16 sector1TimeMS (2)
        # uint8 sector1TimeMin (1)
        # uint16 sector2TimeMS (2)
        # uint8 sector2TimeMin (1)
        # uint16 deltaCarFrontMS (2)
        # uint8 deltaCarFrontMin (1)
        # uint16 deltaRaceLeaderMS (2)
        # uint8 deltaRaceLeaderMin (1)
        # float lapDistance (4)
        # float totalDistance (4)
        # float safetyCarDelta (4)
        # uint8 carPosition (1)
        # uint8 currentLapNum (1)
        # uint8 pitStatus (1)
        # uint8 numPitStops (1)
        # uint8 sector (1)
        # uint8 currentLapInvalid (1)
        # uint8 penalties (1)
        # uint8 totalWarnings (1)
        # uint8 cornerCuttingWarnings (1)
        # uint8 numUnservedDriveThroughPens (1)
        # uint8 numUnservedStopGoPens (1)
        # uint8 gridPosition (1)
        # uint8 driverStatus (1)
        # uint8 resultStatus (1)
        # uint8 pitLaneTimerActive (1)
        # uint16 pitLaneTimeInLaneInMS (2)
        # uint16 pitStopTimerInMS (2)
        # uint8 pitStopShouldServePen (1)
        # float speedTrapFastestSpeed (4)
        # uint8 speedTrapFastestLap (1)
        
        # Summing data types:
        # 4+4+2+1+2+1+2+1+2+1+4+4+4+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+2+2+1+4+1
        # = 57 bytes? Wait.
        # Let's re-verify alignment. Usually packed(1).
        # Let's assume standard packing.
        # Actually in C++ struct usually aligns to 4 bytes. But F1 spec is usually packed 1-byte aligned.
        # Let's assume packed.
        # 4*6 + 2*5 + 1*19 + 4 = 24+10+19+4 = 57... actually 58?
        
        # Wait, let's look at the struct again.
        # 212: uint32 lastLapTimeInMS
        # 213: uint32 currentLapTimeInMS
        # 214: uint16 sector1TimeMSPart
        # 215: uint8 sector1TimeMinutesPart
        # 216: uint16 sector2TimeMSPart
        # 217: uint8 sector2TimeMinutesPart
        # 218: uint16 deltaToCarInFrontMSPart
        # 219: uint8 deltaToCarInFrontMinutesPart
        # 220: uint16 deltaToRaceLeaderMSPart
        # 221: uint8 deltaToRaceLeaderMinutesPart
        # 222: float lapDistance
        # 223: float totalDistance
        # 224: float safetyCarDelta
        # 225: uint8 carPosition
        # 226: uint8 currentLapNum
        # 227: uint8 pitStatus
        # 228: uint8 numPitStops
        # 229: uint8 sector
        # 230: uint8 currentLapInvalid
        # 231: uint8 penalties
        # 232: uint8 totalWarnings
        # 233: uint8 cornerCuttingWarnings
        # 234: uint8 numUnservedDriveThroughPens
        # 235: uint8 numUnservedStopGoPens
        # 236: uint8 gridPosition
        # 237: uint8 driverStatus
        # 238: uint8 resultStatus
        # 239: uint8 pitLaneTimerActive
        # 240: uint16 pitLaneTimeInLaneInMS
        # 241: uint16 pitStopTimerInMS
        # 242: uint8 pitStopShouldServePen
        # 243: float speedTrapFastestSpeed
        # 244: uint8 speedTrapFastestLap
        
        # Bytes:
        # 4, 4, 2, 1, 2, 1, 2, 1, 2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 4, 1
        # Total = 8+3+3+3+3+12+14+4+1+4+1 = 57 bytes exactly.
        
        # PacketLapData has cs_maxNumCarsInUDPData (22) * LapData
        # Offset for player car = player_index * 57
        
        offset = player_index * 57
        if offset + 57 > len(payload):
            return

        car_data = payload[offset : offset + 57]
        # Unpack specific fields we want
        # We want: position (byte 36?), currentLapNum (37?), pitStatus (38?), penalties (41?)
        # Let's just unpack all with custom fmt
        fmt = "<IIHBHBHBHBfffBBBBBBBBBBBBBBBHHBfB"
        try:
            unpacked = struct.unpack(fmt, car_data)
            self.data["lap_data"] = {
                "last_lap_time": unpacked[0],
                "current_lap_time": unpacked[1],
                "last_lap_str": self._format_lap_time(unpacked[0]),
                "car_position": unpacked[22],
                "current_lap_num": unpacked[23],
                "pit_status": unpacked[24],
                "sector": unpacked[26],
                "current_lap_invalid": unpacked[27],
                "penalties": unpacked[28],
            }
            
            # Find current leader's driver index
            struct_size = 57 # Size of LapData in PacketLapData is 57 bytes
            for i in range(22):
                l_offset = i * struct_size
                if l_offset + 23 < len(payload):
                    pos = payload[l_offset + 22]
                    if pos == 1:
                        self.data["session"]["leader_index"] = i
                        break
        except struct.error:
            pass

    def parse_car_telemetry_packet(self, payload: bytes, player_index: int):
        """Parse car telemetry."""
        # CarTelemetryData struct size
        # uint16 speed (2)
        # float throttle (4)
        # float steer (4)
        # float brake (4)
        # uint8 clutch (1)
        # int8 gear (1)
        # uint16 engineRPM (2)
        # uint8 drs (1)
        # uint8 revLightsPercent (1)
        # uint16 revLightsBitValue (2)
        # uint16 brakesTemperature[4] (8)
        # uint8 tyresSurfaceTemperature[4] (4)
        # uint8 tyresInnerTemperature[4] (4)
        # uint16 engineTemperature (2)
        # float tyresPressure[4] (16)
        # uint8 surfaceType[4] (4)
        
        # Total = 2+4+4+4+1+1+2+1+1+2+8+4+4+2+16+4 = 60 bytes exactly.
        
        offset = player_index * 60
        if offset + 60 > len(payload):
            return
            
        car_data = payload[offset : offset + 60]
        fmt = "<HfffBbHBHHHHHHHHHHBBBBBBBBHffffBBBB" # Roughly right, let's simplify for just what we need
        # Speed is first 2 bytes.
        # Throttle 2-6
        # Brake 10-14
        # Gear 15 (1 byte)
        # RPM 16-18 (2 bytes)
        # DRS 18 (1 byte)
        
        # Let's map simpler
        try:
            speed = struct.unpack_from("<H", car_data, 0)[0]
            throttle = struct.unpack_from("<f", car_data, 2)[0]
            brake = struct.unpack_from("<f", car_data, 10)[0]
            gear = struct.unpack_from("<b", car_data, 15)[0]
            rpm = struct.unpack_from("<H", car_data, 16)[0]
            drs = struct.unpack_from("<B", car_data, 18)[0]
            
            self.data["car_telemetry"] = {
                "speed": speed,
                "throttle": throttle,
                "brake": brake,
                "gear": gear,
                "engine_rpm": rpm,
                "drs": drs,
                "tyre_surface_temp": [
                    struct.unpack_from("<B", car_data, 30)[0], # RL
                    struct.unpack_from("<B", car_data, 31)[0], # RR
                    struct.unpack_from("<B", car_data, 32)[0], # FL
                    struct.unpack_from("<B", car_data, 33)[0], # FR
                ],
            }
        except struct.error:
            pass

    def parse_car_status_packet(self, payload: bytes, player_index: int):
        """Parse car status."""
        # CarStatusData struct
        # uint8 tractionControl
        # uint8 antiLockBrakes
        # uint8 fuelMix
        # uint8 frontBrakeBias
        # uint8 pitLimiterStatus
        # float fuelInTank
        # float fuelCapacity
        # float fuelRemainingLaps
        # uint16 maxRPM
        # uint16 idleRPM
        # uint8 maxGears
        # uint8 drsAllowed
        # uint16 drsActivationDistance
        # uint8 actualTyreCompound
        # uint8 visualTyreCompound
        # uint8 tyresAgeLaps
        # int8 vehicleFIAFlags
        # ... and more
        
        # Sizes:
        # 1+1+1+1+1 + 4+4+4 + 2+2+1+1+2+1+1+1+1 = 29 bytes to vehicleFIAFlags
        
        # Total size is 1239 / 22 cars = 56.something? No wait. 
        # Header is 29. Packet - 29 = 1210. 1210 / 22 = 55 bytes per car.
        
        struct_size = 55
        offset = player_index * struct_size
        if offset + struct_size > len(payload):
            return

        car_data = payload[offset : offset + struct_size]
        try:
            pit_limiter = struct.unpack_from("<B", car_data, 4)[0]
            fuel_remaining = struct.unpack_from("<f", car_data, 13)[0] # offset 5 bytes + 2 floats (8) = 13?
            # 0: TC
            # 1: ABS
            # 2: FuelMix
            # 3: FrontBias
            # 4: PitLim
            # 5-8: FuelInTank
            # 9-12: FuelCap
            # 13-16: FuelRemLaps
            
            fia_flags = struct.unpack_from("<b", car_data, 28)[0] # let's check offset
            # 17-18: MaxRPM
            # 19-20: IdleRPM
            # 21: MaxGears
            # 22: DRSAllowed
            # 23-24: DRSDist
            # 25: ActualTyre
            # 26: VisualTyre
            # 27: TyreAge
            # 28: FIAFlags
            
            self.data["car_status"] = {
                "pit_limiter_status": pit_limiter,
                "fuel_remaining_laps": fuel_remaining,
                "fia_flags": fia_flags,
                "tyre_visual": struct.unpack_from("<B", car_data, 26)[0],
                "tyre_age": struct.unpack_from("<B", car_data, 27)[0],
                "ers_store": struct.unpack_from("<f", car_data, 37)[0], # ERS Store is at 37
                "ers_deploy_mode": struct.unpack_from("<B", car_data, 41)[0], # ERS Mode is at 41
                "drs_allowed": struct.unpack_from("<B", car_data, 22)[0],
                "network_paused": car_data[54] if len(car_data) > 54 else 0,
            }
        except struct.error:
            pass

    def parse_car_damage_packet(self, payload: bytes, player_index: int):
        """Parse car damage."""
        # CarDamageData struct size = 46 bytes
        struct_size = 46
        offset = player_index * struct_size
        if offset + struct_size > len(payload):
            return

        car_data = payload[offset : offset + struct_size]
        try:
            # RL, RR, FL, FR
            tyres_wear = struct.unpack("<ffff", car_data[:16])
            terminal = self.data["car_damage"].get("terminal", 0) # Preserve if set by event
            self.data["car_damage"] = {
                "tyres_wear": list(tyres_wear),
                "front_left_wing": car_data[28],
                "front_right_wing": car_data[29],
                "rear_wing": car_data[30],
                "floor": car_data[31],
                "diffuser": car_data[32],
                "sidepod": car_data[33],
                "terminal": terminal,
            }
            has_damage = any([
                any(car_data[16:20]), # tyre damage
                car_data[28], car_data[29], car_data[30], # wings
                car_data[31], car_data[32], car_data[33], # floor etc
            ])
            self.data["car_damage"]["has_damage"] = 1 if has_damage else 0
        except struct.error:
            pass

    def parse_event_packet(self, payload: bytes):
        """Parse event packet."""
        try:
            event_code = payload[:4].decode("ascii")
            if event_code == "STLG": # Start Lights
                num_lights = payload[4]
                self.data["events"]["start_lights"] = num_lights
            elif event_code == "LGOT": # Lights Out
                self.data["events"]["start_lights"] = 0
            elif event_code == "SSTA": self.data["events"]["session_status"] = "Started"
            elif event_code == "SEND": self.data["events"]["session_status"] = "Ended"
            elif event_code == "CHQF": self.data["events"]["session_status"] = "Chequered Flag"
            elif event_code == "FTLP":
                veh_idx = payload[4]
                lap_time = struct.unpack_from("<f", payload, 5)[0]
                self.data["fastest_lap"] = {"car_index": veh_idx, "lap_time": lap_time}
            elif event_code == "RTMT":
                veh_idx = payload[4]
                reason = payload[5]
                if veh_idx == self.data.get("player_car_index") and reason == 3:
                    self.data["car_damage"]["terminal"] = 1
        except (struct.error, UnicodeDecodeError):
            pass

    def parse_participants_packet(self, payload: bytes):
        """Parse participants names."""
        # ParticipantData is 57 bytes
        try:
            num_cars = payload[0]
            for i in range(num_cars):
                offset = 1 + (i * 57)
                if offset + 57 <= len(payload):
                    # Name is at offset 7 in ParticipantData, 32 bytes
                    name_bytes = payload[offset + 7 : offset + 7 + 32]
                    try:
                        name = name_bytes.split(b'\x00')[0].decode("utf-8")
                        self.data["participants"][i] = name
                    except UnicodeDecodeError:
                        pass
        except struct.error:
            pass

    def _format_lap_time(self, lap_time_ms: int) -> str:
        """Format lap time from MS (int) to string mm:ss.ms."""
        if lap_time_ms <= 0:
            return "0:00.000"
        seconds = (lap_time_ms / 1000.0) % 60
        minutes = int((lap_time_ms / (1000.0 * 60)) % 60)
        return f"{minutes}:{seconds:06.3f}"


class F125Protocol(asyncio.DatagramProtocol):
    """UDP Protocol for F1 25."""

    def __init__(self, callback_func):
        """Initialize."""
        self.callback = callback_func

    def connection_made(self, transport):
        """Connection made."""
        self.transport = transport

    def datagram_received(self, data, addr):
        """Datagram received."""
        self.callback(data)
