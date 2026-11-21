"""Live iRacing telemetry adapter using the community pyirsdk wrapper."""
import math

WHEEL_SPEED_VARIABLES = ("LFspeed", "RFspeed", "LRspeed", "RRspeed")
REQUIRED_VARIABLES = ("Speed", "Brake", "Throttle", *WHEEL_SPEED_VARIABLES)
WEAR_VARIABLES = tuple(
    f"{corner}wear{zone}"
    for corner in ("LF", "RF", "LR", "RR")
    for zone in ("L", "M", "R")
)


def decode_iracing_values(values):
    """Normalize iRacing values (m/s, 0..1 pedals) to the app data contract."""
    speed_ms = max(0.0, float(values["Speed"]))
    brake = max(0.0, min(1.0, float(values["Brake"])))
    throttle = max(0.0, min(1.0, float(values["Throttle"])))
    wheel_speeds = tuple(abs(float(values[name])) for name in WHEEL_SPEED_VARIABLES)
    if not all(math.isfinite(v) for v in (speed_ms, brake, throttle, *wheel_speeds)):
        raise ValueError("iRacing returned non-finite telemetry")
    if speed_ms >= 3.0:
        slips = tuple(max(0.0, min(1.0, (speed_ms - wheel_speed) / speed_ms))
                      for wheel_speed in wheel_speeds)
    else:
        slips = (0.0, 0.0, 0.0, 0.0)
    result = {
        "speed_kmh": speed_ms * 3.6,
        "brake": brake,
        "throttle": throttle,
        "wheel_slips": slips,
        "wheel_speeds": wheel_speeds,
    }
    if all(name in values for name in WEAR_VARIABLES):
        wear = []
        for corner in ("LF", "RF", "LR", "RR"):
            remaining = [float(values[f"{corner}wear{zone}"]) for zone in ("L", "M", "R")]
            if not all(math.isfinite(v) for v in remaining):
                break
            # iRacing reports percent tread remaining at inner/middle/outer.
            average_remaining = sum(max(0.0, min(100.0, v)) for v in remaining) / 3.0
            wear.append(1.0 - average_remaining / 100.0)
        if len(wear) == 4:
            result["wheel_wear"] = tuple(wear)
    return result


class IRacingTelemetryReader:
    """Connect/retry through pyirsdk; iRacing publishes live data at 60 Hz."""
    def __init__(self):
        try:
            import irsdk
        except ImportError as exc:
            raise RuntimeError(
                "Dépendance iRacing absente : installe les dépendances avec "
                "'pip install -r requirements.txt' (pyirsdk)."
            ) from exc
        self.sdk = irsdk.IRSDK()
        if not self.sdk.startup():
            self.sdk.shutdown()
            raise RuntimeError("iRacing n'est pas encore connecté ou sa télémétrie n'est pas disponible.")
        names = set(self.sdk.var_headers_names)
        missing = [name for name in REQUIRED_VARIABLES if name not in names]
        if missing:
            self.sdk.shutdown()
            raise RuntimeError("Variables iRacing manquantes : " + ", ".join(missing))
        self.wear_variables = tuple(name for name in WEAR_VARIABLES if name in names)
        self.last_tick = None

    def read(self):
        if not self.sdk.is_initialized or not self.sdk.is_connected:
            raise RuntimeError("Connexion iRacing perdue.")
        tick = self.sdk._header.cur_buf_tick_count
        if tick == self.last_tick:
            return None
        self.last_tick = tick
        values = {name: self.sdk[name] for name in (*REQUIRED_VARIABLES, *self.wear_variables)}
        return decode_iracing_values(values)

    def close(self):
        try:
            self.sdk.shutdown()
        except Exception:
            pass
