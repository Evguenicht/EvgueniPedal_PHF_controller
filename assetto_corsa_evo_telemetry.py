"""Assetto Corsa EVO shared-memory reader (Windows, read-only).

Reads the physics page published by AC EVO:
  Local\\acevo_pmf_physics
The field offsets below follow the publicly documented SPageFilePhysics layout.
Wheel order is FL, FR, RL, RR.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import math
import struct
import sys

PHYSICS_MAPPING_NAME = r"Local\acevo_pmf_physics"
PHYSICS_MAP_SIZE = 4096
PHYSICS_DOCUMENTED_SIZE = 800

# SPageFilePhysics offsets (little-endian, pack=4).
OFF_PACKET_ID = 0
OFF_GAS = 4
OFF_BRAKE = 8
OFF_SPEED_KMH = 28
OFF_WHEEL_COMBINED_SLIP = 56
OFF_WHEEL_LOAD = 72
OFF_WHEEL_ANGULAR_SPEED = 104
OFF_LONGITUDINAL_SLIP_RATIO = 640
OFF_ABS_IN_ACTION = 676


def decode_physics_page(raw: bytes, previous_packet_id=None):
    """Decode one physics page into the common MOZA telemetry contract.

    `slipRatio` is the per-wheel longitudinal slip supplied by ACEVO. Its
    magnitude is bounded to 0..1 for the existing WheelTracker interface;
    raw signed values are retained for calibration during in-game tests.
    """
    if len(raw) < PHYSICS_DOCUMENTED_SIZE:
        raise ValueError(f"ACEVO physics page too short: {len(raw)} bytes")

    packet_id = struct.unpack_from('<i', raw, OFF_PACKET_ID)[0]
    if previous_packet_id is not None and packet_id == previous_packet_id:
        return None

    gas = struct.unpack_from('<f', raw, OFF_GAS)[0]
    brake = struct.unpack_from('<f', raw, OFF_BRAKE)[0]
    speed_kmh = struct.unpack_from('<f', raw, OFF_SPEED_KMH)[0]
    combined_slip = struct.unpack_from('<4f', raw, OFF_WHEEL_COMBINED_SLIP)
    wheel_load = struct.unpack_from('<4f', raw, OFF_WHEEL_LOAD)
    wheel_angular_speed = struct.unpack_from('<4f', raw, OFF_WHEEL_ANGULAR_SPEED)
    slip_ratio_raw = struct.unpack_from('<4f', raw, OFF_LONGITUDINAL_SLIP_RATIO)
    abs_in_action = struct.unpack_from('<i', raw, OFF_ABS_IN_ACTION)[0]

    numeric = (gas, brake, speed_kmh, *combined_slip, *wheel_load,
               *wheel_angular_speed, *slip_ratio_raw)
    if not all(math.isfinite(float(v)) for v in numeric):
        raise ValueError("ACEVO returned non-finite physics telemetry")
    if not (-5.0 <= speed_kmh <= 600.0):
        raise ValueError(f"ACEVO speed out of range: {speed_kmh}")

    gas = max(0.0, min(1.0, float(gas)))
    brake = max(0.0, min(1.0, float(brake)))
    speed_kmh = max(0.0, float(speed_kmh))
    wheel_slips = tuple(max(0.0, min(1.0, abs(float(v)))) for v in slip_ratio_raw)

    return {
        "packet_id": packet_id,
        "speed_kmh": speed_kmh,
        "brake": brake,
        "throttle": gas,
        "wheel_slips": wheel_slips,
        "wheel_slip_ratio_raw": tuple(float(v) for v in slip_ratio_raw),
        "wheel_combined_slip": tuple(float(v) for v in combined_slip),
        "wheel_load": tuple(float(v) for v in wheel_load),
        "wheel_angular_speeds": tuple(float(v) for v in wheel_angular_speed),
        "abs_in_action": bool(abs_in_action),
        "wheel_order": ("FL", "FR", "RL", "RR"),
    }


class ACEvoTelemetryReader:
    """Attach read-only to AC EVO's physics shared-memory mapping."""
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Assetto Corsa EVO shared memory is available on Windows only")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenFileMappingW.restype = wintypes.HANDLE
        self.kernel32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel32.MapViewOfFile.restype = wintypes.LPVOID
        self.kernel32.MapViewOfFile.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t
        ]
        self.kernel32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        self.handle = self.kernel32.OpenFileMappingW(
            0x0004, False, PHYSICS_MAPPING_NAME  # FILE_MAP_READ
        )
        if not self.handle:
            error = ctypes.get_last_error()
            raise FileNotFoundError(
                error, "AC EVO physics mapping not found; start a driving session",
                PHYSICS_MAPPING_NAME
            )
        self.address = self.kernel32.MapViewOfFile(
            self.handle, 0x0004, 0, 0, PHYSICS_MAP_SIZE
        )
        if not self.address:
            error = ctypes.get_last_error()
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
            raise OSError(error, "Unable to map AC EVO physics page")
        self.last_packet_id = None

    def read(self):
        raw = ctypes.string_at(self.address, PHYSICS_DOCUMENTED_SIZE)
        data = decode_physics_page(raw, self.last_packet_id)
        if data is not None:
            self.last_packet_id = data["packet_id"]
        return data

    def close(self):
        if getattr(self, "address", None):
            self.kernel32.UnmapViewOfFile(self.address)
            self.address = None
        if getattr(self, "handle", None):
            self.kernel32.CloseHandle(self.handle)
            self.handle = None

