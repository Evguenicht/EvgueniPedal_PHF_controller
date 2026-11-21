"""Automobilista 2 shared-memory telemetry adapter (Windows, read-only).

Uses the Project CARS 2 shared-memory layout selected in AMS2 settings.
Layout offsets are derived from the Reiza/SMS SharedMemory.h structure
(version 14). The reader validates the version and uses mSequenceNumber
to avoid consuming a page while the game is writing it.

Important: the shared-memory header marks mTyreSlipSpeed and mTyreGrip as
OBSOLETE. They are exposed for diagnostics only, never used as detector input.
The current wheel-slip estimate is a relative wheel-speed deficit based on
mTyreRPS and the fastest of the four wheels; it is not an absolute physical
longitudinal slip ratio and must be validated in-game.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import math
import struct
import sys

SHARED_MEMORY_NAME = "$pcars2$"
SUPPORTED_SHARED_MEMORY_VERSION = 14

# Offsets calculated with the default 4-byte alignment of the C SharedMemory
# structure (including ParticipantInfo[64]); checked against header v14.
OFF_VERSION = 0
OFF_GAME_STATE = 8
OFF_CAR_NAME = 6444
OFF_CAR_CLASS_NAME = 6508
OFF_SPEED_MS = 6848
OFF_BRAKE = 6860
OFF_THROTTLE = 6864
OFF_ABS_ACTIVE = 6888
OFF_LOCAL_VELOCITY = 6920
OFF_TYRE_FLAGS = 6992
OFF_TYRE_RPS = 7040
OFF_TYRE_SLIP_SPEED_OBSOLETE = 7056
OFF_TYRE_GRIP_OBSOLETE = 7088
OFF_TYRE_WEAR = 7136  # mTyreWear[4], 0.0 = neuf, 1.0 = usé
OFF_SEQUENCE_NUMBER = 7320
MINIMUM_PAGE_SIZE = OFF_SEQUENCE_NUMBER + 4

GAME_INGAME_PLAYING = 2
WHEEL_ORDER = ("FL", "FR", "RL", "RR")
MIN_SPEED_FOR_SLIP_KMH = 10.0


def _read_c_string(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("utf-8", errors="replace").strip()


def _finite_values(values, label):
    result = tuple(float(v) for v in values)
    if not all(math.isfinite(v) for v in result):
        raise ValueError(f"AMS2 returned non-finite {label}")
    return result


def decode_ams2_page(raw: bytes, previous_sequence=None):
    """Decode one stable SharedMemory v14 snapshot into the common app schema."""
    if len(raw) < MINIMUM_PAGE_SIZE:
        raise ValueError(
            f"AMS2 shared-memory page too short: {len(raw)} bytes; "
            f"at least {MINIMUM_PAGE_SIZE} required"
        )

    version = struct.unpack_from("<I", raw, OFF_VERSION)[0]
    if version != SUPPORTED_SHARED_MEMORY_VERSION:
        raise RuntimeError(
            f"AMS2 shared-memory version {version} unsupported; "
            f"expected {SUPPORTED_SHARED_MEMORY_VERSION}"
        )

    game_state = struct.unpack_from("<I", raw, OFF_GAME_STATE)[0]
    sequence = struct.unpack_from("<I", raw, OFF_SEQUENCE_NUMBER)[0]
    if sequence & 1:
        return None
    if previous_sequence is not None and sequence == previous_sequence:
        return None
    if game_state != GAME_INGAME_PLAYING:
        return None

    speed_ms = struct.unpack_from("<f", raw, OFF_SPEED_MS)[0]
    brake = struct.unpack_from("<f", raw, OFF_BRAKE)[0]
    throttle = struct.unpack_from("<f", raw, OFF_THROTTLE)[0]
    abs_active = bool(struct.unpack_from("<?", raw, OFF_ABS_ACTIVE)[0])
    local_velocity = _finite_values(
        struct.unpack_from("<3f", raw, OFF_LOCAL_VELOCITY), "local_velocity"
    )
    tyre_flags = struct.unpack_from("<4I", raw, OFF_TYRE_FLAGS)
    tyre_rps = _finite_values(struct.unpack_from("<4f", raw, OFF_TYRE_RPS), "tyre_rps")
    tyre_slip_speed = _finite_values(
        struct.unpack_from("<4f", raw, OFF_TYRE_SLIP_SPEED_OBSOLETE), "tyre_slip_speed"
    )
    tyre_grip = _finite_values(
        struct.unpack_from("<4f", raw, OFF_TYRE_GRIP_OBSOLETE), "tyre_grip"
    )
    tyre_wear_raw = _finite_values(
        struct.unpack_from("<4f", raw, OFF_TYRE_WEAR), "tyre_wear"
    )
    # SharedMemory.h: mTyreWear is a fraction in [0, 1], 0 = new, 1 = worn.
    wheel_wear = tuple(max(0.0, min(1.0, value)) for value in tyre_wear_raw)

    if not all(math.isfinite(v) for v in (speed_ms, brake, throttle)):
        raise ValueError("AMS2 returned non-finite speed or pedal values")
    if not 0.0 <= speed_ms <= 200.0:
        raise ValueError(f"AMS2 speed out of range: {speed_ms} m/s")
    if not -0.05 <= brake <= 1.05 or not -0.05 <= throttle <= 1.05:
        raise ValueError(f"AMS2 pedal value out of range: brake={brake}, throttle={throttle}")

    # A second sequence read is performed by the live reader. This pure decoder
    # also accepts synthetic snapshots for deterministic tests.
    speed_kmh = max(0.0, float(speed_ms)) * 3.6
    rps_abs = tuple(abs(v) for v in tyre_rps)
    max_rps = max(rps_abs, default=0.0)
    if speed_kmh >= MIN_SPEED_FOR_SLIP_KMH and max_rps > 0.5:
        # Relative loss versus the fastest wheel. This detects a single wheel
        # slowing down substantially; it is deliberately not labelled as a
        # physical slip ratio because AMS2 no longer documents tyre radius or
        # an active per-wheel linear speed channel in this shared-memory API.
        wheel_slips = tuple(
            max(0.0, min(1.0, 1.0 - (wheel_rps / max_rps)))
            for wheel_rps in rps_abs
        )
    else:
        wheel_slips = (0.0, 0.0, 0.0, 0.0)

    return {
        "packet_id": sequence,
        "speed_kmh": speed_kmh,
        "brake": max(0.0, min(1.0, float(brake))),
        "throttle": max(0.0, min(1.0, float(throttle))),
        "wheel_slips": wheel_slips,
        "wheel_rps": tyre_rps,
        "wheel_slip_speed_obsolete": tyre_slip_speed,
        "wheel_grip_obsolete": tyre_grip,
        "wheel_wear": wheel_wear,
        "wheel_flags": tuple(int(v) for v in tyre_flags),
        "local_velocity_ms": local_velocity,
        "abs_active": abs_active,
        "vehicle_name": _read_c_string(raw[OFF_CAR_NAME:OFF_CAR_NAME + 64]),
        "vehicle_class": _read_c_string(raw[OFF_CAR_CLASS_NAME:OFF_CAR_CLASS_NAME + 64]),
        "shared_memory_version": version,
        "wheel_order": WHEEL_ORDER,
        "slip_method": "relative_rps_to_fastest_wheel",
    }


class AMS2TelemetryReader:
    """Attach read-only to AMS2's $pcars2$ Windows shared-memory mapping."""
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("AMS2 shared memory is available on Windows only")

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenFileMappingW.restype = wintypes.HANDLE
        self.kernel32.OpenFileMappingW.argtypes = [
            wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR
        ]
        self.kernel32.MapViewOfFile.restype = wintypes.LPVOID
        self.kernel32.MapViewOfFile.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t
        ]
        self.kernel32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        self.handle = self.kernel32.OpenFileMappingW(
            0x0004, False, SHARED_MEMORY_NAME  # FILE_MAP_READ
        )
        if not self.handle:
            error = ctypes.get_last_error()
            raise FileNotFoundError(
                error,
                "AMS2 $pcars2$ shared memory not found; enable Project CARS 2 shared memory and start a driving session",
            )

        self.address = self.kernel32.MapViewOfFile(
            self.handle, 0x0004, 0, 0, 0
        )
        if not self.address:
            error = ctypes.get_last_error()
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
            raise OSError(error, "Unable to map AMS2 shared memory")

        self.last_sequence = None
        header = ctypes.string_at(self.address, 4)
        version = struct.unpack("<I", header)[0]
        if version != SUPPORTED_SHARED_MEMORY_VERSION:
            self.close()
            raise RuntimeError(
                f"AMS2 shared-memory version {version} unsupported; "
                f"expected {SUPPORTED_SHARED_MEMORY_VERSION}"
            )

    def read(self):
        # Sequence counter is odd during writes and even after a completed frame.
        seq_before = struct.unpack(
            "<I", ctypes.string_at(self.address + OFF_SEQUENCE_NUMBER, 4)
        )[0]
        if seq_before & 1 or seq_before == self.last_sequence:
            return None
        raw = ctypes.string_at(self.address, MINIMUM_PAGE_SIZE)
        seq_after = struct.unpack(
            "<I", ctypes.string_at(self.address + OFF_SEQUENCE_NUMBER, 4)
        )[0]
        if seq_before != seq_after or (seq_after & 1):
            return None
        data = decode_ams2_page(raw, self.last_sequence)
        if data is not None:
            self.last_sequence = data["packet_id"]
        return data

    def close(self):
        if getattr(self, "address", None):
            self.kernel32.UnmapViewOfFile(self.address)
            self.address = None
        if getattr(self, "handle", None):
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
