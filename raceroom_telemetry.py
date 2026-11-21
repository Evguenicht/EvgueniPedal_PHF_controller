"""RaceRoom Racing Experience shared-memory telemetry adapter.

Layout based on the official KW Studios r3e-api C header (API 3.6):
https://github.com/kwstudios-sweden/r3e-api

Shared memory name: $R3E. All structures are packed (pack=1).
The reader uses the player block only and never writes to the mapping.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import math
import struct
import sys

SHARED_MEMORY_NAME = b"$R3E"
API_MAJOR_SUPPORTED = 3
API_MINOR_MINIMUM = 6

# Offsets in the official r3e.h v3.6 layout (pack=1).
OFF_VERSION_MAJOR = 0
OFF_VERSION_MINOR = 4
OFF_ALL_DRIVERS_OFFSET = 8
OFF_DRIVER_DATA_SIZE = 12
OFF_GAME_PAUSED = 20
OFF_GAME_IN_MENUS = 24
OFF_GAME_IN_REPLAY = 28
OFF_GAME_PLAYER_IN_GARAGE = 36
OFF_PLAYER_SIMULATION_TICKS = 44
OFF_VEHICLE_INFO = 1196
OFF_VEHICLE_CLASS_ID = 1264
OFF_CONTROL_TYPE = 1388
OFF_CAR_SPEED_MS = 1392
OFF_THROTTLE = 1500
OFF_BRAKE = 1508
OFF_ABS_STATE = 1536  # aid_settings.abs: -1 N/A, 0 off, 1 on, 5 active
OFF_ABS_SETTING = 1616  # -1 N/A; car-specific ABS setting
OFF_TIRE_RPS = 1632
OFF_TIRE_SPEED_MS = 1648
OFF_TIRE_GRIP = 1664
OFF_BRAKE_PRESSURE_KN = 1920
OFF_TIRE_LOAD_N = 1968
OFF_NUM_CARS_EXPECTED = 2008
MINIMUM_PAGE_SIZE = 1984
MAP_VIEW_SIZE = 0  # 0 maps the complete shared-memory object.

WHEEL_ORDER = ("FL", "FR", "RL", "RR")


def _finite_tuple(values, label):
    result = tuple(float(v) for v in values)
    if not all(math.isfinite(v) for v in result):
        raise ValueError(f"RaceRoom returned non-finite {label}")
    return result


def decode_raceroom_page(raw: bytes, previous_ticks=None):
    """Decode one RaceRoom 3.6 shared-memory page into the app data contract."""
    if len(raw) < MINIMUM_PAGE_SIZE:
        raise ValueError(f"RaceRoom shared-memory page too short: {len(raw)} bytes")

    major, minor, all_drivers_offset, driver_data_size = struct.unpack_from("<4i", raw, 0)
    if major != API_MAJOR_SUPPORTED or minor < API_MINOR_MINIMUM:
        raise RuntimeError(
            f"RaceRoom Shared Memory API {major}.{minor} unsupported; "
            f"version {API_MAJOR_SUPPORTED}.{API_MINOR_MINIMUM}+ required"
        )
    if all_drivers_offset != OFF_NUM_CARS_EXPECTED:
        raise RuntimeError(
            "RaceRoom shared-memory layout mismatch: expected num_cars at "
            f"{OFF_NUM_CARS_EXPECTED}, received {all_drivers_offset}. "
            "The API layout may have changed."
        )
    if not 0 < driver_data_size < 4096:
        raise RuntimeError(f"Invalid RaceRoom driver_data_size: {driver_data_size}")

    paused = struct.unpack_from("<i", raw, OFF_GAME_PAUSED)[0]
    in_menus = struct.unpack_from("<i", raw, OFF_GAME_IN_MENUS)[0]
    in_replay = struct.unpack_from("<i", raw, OFF_GAME_IN_REPLAY)[0]
    in_garage = struct.unpack_from("<i", raw, OFF_GAME_PLAYER_IN_GARAGE)[0]
    ticks = struct.unpack_from("<i", raw, OFF_PLAYER_SIMULATION_TICKS)[0]
    if previous_ticks is not None and ticks == previous_ticks:
        return None
    if paused or in_menus or in_replay or in_garage:
        return None

    # R3E control_type: 0 = actual player, 1 = AI, 2 = remote, 3 = replay/ghost.
    control_type = struct.unpack_from("<i", raw, OFF_CONTROL_TYPE)[0]
    if control_type != 0:
        return None

    class_id = struct.unpack_from("<i", raw, OFF_VEHICLE_CLASS_ID)[0]
    name_raw = raw[OFF_VEHICLE_INFO:OFF_VEHICLE_INFO + 64]
    vehicle_name = name_raw.split(b"\0", 1)[0].decode("utf-8", errors="replace").strip()

    speed_ms = struct.unpack_from("<f", raw, OFF_CAR_SPEED_MS)[0]
    throttle = struct.unpack_from("<f", raw, OFF_THROTTLE)[0]
    brake = struct.unpack_from("<f", raw, OFF_BRAKE)[0]
    abs_state = struct.unpack_from("<i", raw, OFF_ABS_STATE)[0]
    abs_setting = struct.unpack_from("<i", raw, OFF_ABS_SETTING)[0]
    tire_rps = _finite_tuple(struct.unpack_from("<4f", raw, OFF_TIRE_RPS), "tire_rps")
    tire_speed = _finite_tuple(struct.unpack_from("<4f", raw, OFF_TIRE_SPEED_MS), "tire_speed")
    tire_grip = _finite_tuple(struct.unpack_from("<4f", raw, OFF_TIRE_GRIP), "tire_grip")
    brake_pressure = _finite_tuple(struct.unpack_from("<4f", raw, OFF_BRAKE_PRESSURE_KN), "brake_pressure")
    tire_load = _finite_tuple(struct.unpack_from("<4f", raw, OFF_TIRE_LOAD_N), "tire_load")

    if not all(math.isfinite(float(v)) for v in (speed_ms, throttle, brake)):
        raise ValueError("RaceRoom returned non-finite speed or pedal data")
    if not -1.0 <= speed_ms <= 200.0:
        raise ValueError(f"RaceRoom speed out of range: {speed_ms} m/s")

    speed_ms = max(0.0, float(speed_ms))
    # In the official API tire_speed is the linear wheel speed in m/s.
    # Positive slip here means wheel speed is below vehicle speed (braking slip).
    if speed_ms >= 1.0:
        wheel_slips = tuple(
            max(0.0, min(1.0, (speed_ms - abs(wheel_speed)) / speed_ms))
            for wheel_speed in tire_speed
        )
    else:
        wheel_slips = (0.0, 0.0, 0.0, 0.0)

    return {
        "packet_id": ticks,
        "speed_kmh": speed_ms * 3.6,
        "brake": max(0.0, min(1.0, float(brake))),
        "throttle": max(0.0, min(1.0, float(throttle))),
        "wheel_slips": wheel_slips,
        "wheel_speed_ms": tire_speed,
        "wheel_rps": tire_rps,
        "wheel_grip": tire_grip,
        "brake_pressure_kn": brake_pressure,
        "wheel_load_n": tire_load,
        "abs_state": abs_state,
        "abs_setting": abs_setting,
        "vehicle_class_id": class_id,
        "vehicle_name": vehicle_name,
        "api_version": f"{major}.{minor}",
        "wheel_order": WHEEL_ORDER,
    }


class RaceRoomTelemetryReader:
    """Read-only attachment to RaceRoom's $R3E shared-memory mapping."""
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("RaceRoom shared memory is available on Windows only")

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenFileMappingA.restype = wintypes.HANDLE
        self.kernel32.OpenFileMappingA.argtypes = [wintypes.DWORD, wintypes.BOOL, ctypes.c_char_p]
        self.kernel32.MapViewOfFile.restype = wintypes.LPVOID
        self.kernel32.MapViewOfFile.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t
        ]
        self.kernel32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        self.handle = self.kernel32.OpenFileMappingA(0x0004, False, SHARED_MEMORY_NAME)
        if not self.handle:
            error = ctypes.get_last_error()
            raise FileNotFoundError(
                error, "RaceRoom $R3E shared memory not found; start a driving session"
            )
        self.address = self.kernel32.MapViewOfFile(
            self.handle, 0x0004, 0, 0, MAP_VIEW_SIZE
        )
        if not self.address:
            error = ctypes.get_last_error()
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
            raise OSError(error, "Unable to map RaceRoom shared memory")
        self.last_ticks = None

        # Fail early on unsupported API versions/layouts before the controller loop.
        header = ctypes.string_at(self.address, 16)
        major, minor, all_drivers_offset, driver_data_size = struct.unpack("<4i", header)
        if major != API_MAJOR_SUPPORTED or minor < API_MINOR_MINIMUM:
            self.close()
            raise RuntimeError(f"RaceRoom API {major}.{minor} unsupported; expected 3.6+")
        if all_drivers_offset != OFF_NUM_CARS_EXPECTED or not 0 < driver_data_size < 4096:
            self.close()
            raise RuntimeError("RaceRoom API layout differs from the verified 3.6 header")

    def read(self):
        raw = ctypes.string_at(self.address, MINIMUM_PAGE_SIZE)
        data = decode_raceroom_page(raw, self.last_ticks)
        if data is not None:
            self.last_ticks = data["packet_id"]
        return data

    def close(self):
        if getattr(self, "address", None):
            self.kernel32.UnmapViewOfFile(self.address)
            self.address = None
        if getattr(self, "handle", None):
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
