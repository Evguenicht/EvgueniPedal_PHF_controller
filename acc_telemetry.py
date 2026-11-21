"""
Assetto Corsa Competizione telemetry reader.
Reads ACC's Windows shared-memory physics page in read-only mode.

ACC's documented physics structure exposes a dedicated per-wheel slipRatio
array. The SDK marks tyreRadius as unused in ACC, so this reader deliberately
does not estimate slip from wheelAngularSpeed * tyreRadius.
"""
import ctypes
import math


PHYSICS_MAP_NAME = "Local\\acpmf_physics"


class _PhysicsACC(ctypes.Structure):
    """ACC SPageFilePhysics fields through slipRatio, packed on 4 bytes."""
    _pack_ = 4
    _fields_ = [
        ("packet_id", ctypes.c_int32),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int32),
        ("rpm", ctypes.c_int32),
        ("steer_angle", ctypes.c_float),
        ("speed_kmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("acc_g", ctypes.c_float * 3),
        ("wheel_slip", ctypes.c_float * 4),
        ("wheel_load", ctypes.c_float * 4),
        ("wheel_pressure", ctypes.c_float * 4),
        ("wheel_angular_speed", ctypes.c_float * 4),
        ("tyre_wear", ctypes.c_float * 4),
        ("tyre_dirty_level", ctypes.c_float * 4),
        ("tyre_core_temp", ctypes.c_float * 4),
        ("camber_rad", ctypes.c_float * 4),
        ("suspension_travel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cg_height", ctypes.c_float),
        ("car_damage", ctypes.c_float * 5),
        ("number_of_tyres_out", ctypes.c_int32),
        ("pit_limiter_on", ctypes.c_int32),
        ("abs", ctypes.c_float),
        ("kers_charge", ctypes.c_float),
        ("kers_input", ctypes.c_float),
        ("autoshifter_on", ctypes.c_int32),
        ("ride_height", ctypes.c_float * 2),
        ("turbo_boost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("air_density", ctypes.c_float),
        ("air_temp", ctypes.c_float),
        ("road_temp", ctypes.c_float),
        ("local_angular_vel", ctypes.c_float * 3),
        ("final_ff", ctypes.c_float),
        ("performance_meter", ctypes.c_float),
        ("engine_brake", ctypes.c_int32),
        ("ers_recovery_level", ctypes.c_int32),
        ("ers_power_level", ctypes.c_int32),
        ("ers_heat_charging", ctypes.c_int32),
        ("ers_is_charging", ctypes.c_int32),
        ("kers_current_kj", ctypes.c_float),
        ("drs_available", ctypes.c_int32),
        ("drs_enabled", ctypes.c_int32),
        ("brake_temp", ctypes.c_float * 4),
        ("clutch", ctypes.c_float),
        ("tyre_temp_i", ctypes.c_float * 4),
        ("tyre_temp_m", ctypes.c_float * 4),
        ("tyre_temp_o", ctypes.c_float * 4),
        ("is_ai_controlled", ctypes.c_int32),
        ("tyre_contact_point", (ctypes.c_float * 3) * 4),
        ("tyre_contact_normal", (ctypes.c_float * 3) * 4),
        ("tyre_contact_heading", (ctypes.c_float * 3) * 4),
        ("brake_bias", ctypes.c_float),
        ("local_velocity", ctypes.c_float * 3),
        ("p2p_activation", ctypes.c_int32),
        ("p2p_status", ctypes.c_int32),
        ("current_max_rpm", ctypes.c_float),
        ("fx", ctypes.c_float * 4),
        ("fy", ctypes.c_float * 4),
        ("slip_ratio", ctypes.c_float * 4),
    ]


def calculate_braking_slip(slip_ratio_values):
    """
    ACC's signed slipRatio is negative under braking and positive under
    acceleration. Convert braking slip to a positive 0..1 magnitude.
    Wheel order: FL, FR, RL, RR.
    """
    if len(slip_ratio_values) != 4:
        raise ValueError("ACC requires exactly four slipRatio values.")
    result = []
    for value in slip_ratio_values:
        value = float(value)
        if not math.isfinite(value):
            value = 0.0
        result.append(max(0.0, min(1.0, -value)))
    return tuple(result)


class ACCTelemetryReader:
    """Read-only ACC shared-memory reader (wheel order FL, FR, RL, RR)."""

    def __init__(self):
        if not hasattr(ctypes, "WinDLL"):
            raise OSError("ACC shared memory is available only on Windows.")

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenFileMappingW.restype = ctypes.c_void_p
        self.kernel32.OpenFileMappingW.argtypes = [
            ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p
        ]
        self.kernel32.MapViewOfFile.restype = ctypes.c_void_p
        self.kernel32.MapViewOfFile.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_uint32, ctypes.c_size_t
        ]
        self.kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

        self.physics_handle = None
        self.physics_address = None
        self.last_packet_id = None
        self._connect()

    def _connect(self):
        self.physics_handle = self.kernel32.OpenFileMappingW(
            0x0004, False, PHYSICS_MAP_NAME
        )
        if not self.physics_handle:
            raise OSError(
                ctypes.get_last_error(),
                "Impossible d'ouvrir Local\\acpmf_physics. "
                "Vérifie qu'ACC est lancé."
            )
        self.physics_address = self.kernel32.MapViewOfFile(
            self.physics_handle, 0x0004, 0, 0,
            ctypes.sizeof(_PhysicsACC)
        )
        if not self.physics_address:
            error = ctypes.get_last_error()
            self.close()
            raise OSError(error, "Impossible de mapper la télémétrie physique ACC.")

    def read(self):
        if not self.physics_address:
            raise OSError("Mémoire physique ACC déconnectée.")

        # Avoid processing a shared-memory buffer while ACC is updating it.
        first_id = ctypes.c_int32.from_address(self.physics_address).value
        raw = ctypes.string_at(
            self.physics_address, ctypes.sizeof(_PhysicsACC)
        )
        second_id = ctypes.c_int32.from_address(self.physics_address).value
        if first_id != second_id:
            return None

        physics = _PhysicsACC.from_buffer_copy(raw)
        packet_id = int(physics.packet_id)
        if packet_id == self.last_packet_id:
            return None
        self.last_packet_id = packet_id

        speed_kmh = max(0.0, float(physics.speed_kmh))
        brake = max(0.0, min(1.0, float(physics.brake)))
        raw_slip_ratio = tuple(float(value) for value in physics.slip_ratio)
        wheel_slips = calculate_braking_slip(raw_slip_ratio)

        return {
            "packet_id": packet_id,
            "speed_kmh": speed_kmh,
            "brake": brake,
            "gas": max(0.0, min(1.0, float(physics.gas))),
            "wheel_slips": wheel_slips,
            "slip_ratio": raw_slip_ratio,
            "wheel_angular_speeds": tuple(
                float(value) for value in physics.wheel_angular_speed
            ),
        }

    def close(self):
        if getattr(self, "physics_address", None):
            try:
                self.kernel32.UnmapViewOfFile(self.physics_address)
            except Exception:
                pass
            self.physics_address = None
        if getattr(self, "physics_handle", None):
            try:
                self.kernel32.CloseHandle(self.physics_handle)
            except Exception:
                pass
            self.physics_handle = None
