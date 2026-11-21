import ctypes
import ctypes.wintypes as wintypes
import serial
import struct
from collections import deque
import time
import socket
from forza_horizon_6 import ForzaUDPReceiver
from f1_26_telemetry import F126UDPReceiver
from iracing_telemetry import IRacingTelemetryReader
from assetto_corsa_evo_telemetry import ACEvoTelemetryReader
from raceroom_telemetry import RaceRoomTelemetryReader
from ams2_telemetry import AMS2TelemetryReader
from acc_telemetry import ACCTelemetryReader


# ============================================================
# CONFIGURATION — chargée depuis l'interface MOZA
# ============================================================

import json
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "EPPHF_settings.json"
ALLOWED_FREQUENCIES = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)

DEFAULT_CONFIG = {
    "game": "LMU",
    "udp_port": 20444,
    "f1_udp_port": 20777,
    "global_brake_warning": {"alert": {"enabled": True, "frequency_hz": 40, "intensity": 20}, "advanced": {"warning_min_speed_kmh": 0.0, "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0, "warning_onset_intercept": 45.0, "warning_max_speed_kmh": 250.0, "warning_max_intercept": 60.0, "warning_max_slope": 0.2}},
    "com_port": "COM7",
    "baudrate": 115200,
    "system_enabled": True,
    "send_rate": 50,
    "read_rate": 333,
    "alerts": {
        "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
        "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40},
        "brake_warning": {"enabled": True, "frequency_hz": 40, "intensity": 20},
    },
    "advanced": {
        "brake_threshold": 0.05,
        "min_slip_threshold": 0.05,
        "slip_threshold": 0.5,
        "slip_derivative_threshold": 0.0,
        "prediction_horizon_ms": 30,
        "warning_min_speed_kmh": 0.0,
        "warning_grip_coefficient": 0.0,
        "warning_wear_coefficient": 0.0,
        "warning_onset_intercept": 45.0,
        "warning_max_speed_kmh": 250.0,
        "warning_max_intercept": 60.0,
        "warning_max_slope": 40.0 / 200.0,
    },
    "lmu_class_warnings": {
        "HYP": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        },
        "LMP2_ELMS": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        },
        "LMP2": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        },
        "LMP3": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        },
        "GTE": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        },
        "GT3": {
                "alerts": {
                "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
                "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40}
        },
        "detection": {
                "brake_threshold": 0.05,
                "min_slip_threshold": 0.05,
                "slip_threshold": 0.5,
                "slip_derivative_threshold": 0.0,
                "prediction_horizon_ms": 30
        },
        "alert": {
                        "enabled": True,
                        "frequency_hz": 40,
                        "intensity": 20
                },
                "advanced": {
                        "warning_min_speed_kmh": 0.0,
                        "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                        "warning_onset_intercept": 45.0,
                        "warning_max_speed_kmh": 250.0,
                        "warning_max_intercept": 60.0,
                        "warning_max_slope": 0.2
                }
        }
},
}


def deep_update(base, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config():
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as file:
                saved = json.load(file)
            if not isinstance(saved, dict):
                raise ValueError("Le fichier doit contenir un objet JSON.")
            if isinstance(saved.get("profiles"), dict):
                selected = str(saved.get("selected_game", "LMU")).upper()
                shared_warning = saved.get("global_brake_warning")
                if isinstance(shared_warning, dict):
                    deep_update(config["global_brake_warning"], shared_warning)
                else:
                    legacy_profile = saved.get("profiles", {}).get(selected, {})
                    legacy_alert = legacy_profile.get("alerts", {}).get("brake_warning", {})
                    legacy_advanced = legacy_profile.get("advanced", {})
                    config["global_brake_warning"]["alert"].update({
                        key: legacy_alert[key] for key in ("enabled", "frequency_hz", "intensity")
                        if key in legacy_alert
                    })
                    for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient",
                                "warning_onset_intercept", "warning_max_intercept", "warning_max_slope"):
                        if key in legacy_advanced:
                            config["global_brake_warning"]["advanced"][key] = legacy_advanced[key]
                    old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                    if old_slope > 0:
                        a = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                        config["global_brake_warning"]["advanced"]["warning_max_speed_kmh"] = max(1.0, (100.0-a)/old_slope)
                if selected not in ("AC", "ACC", "ACR", "LMU", "FH6", "IRACING", "F126", "ACEVO", "R3E", "AMS2"):
                    raise ValueError(f"Profil de jeu inconnu : {selected}")
                profile = saved["profiles"].get(selected, {})
                if isinstance(profile, dict):
                    deep_update(config, profile)
                    if selected == "LMU" and "lmu_class_warnings" not in profile:
                        legacy_alert = profile.get("alerts", {}).get("brake_warning", {})
                        legacy_advanced = profile.get("advanced", {})
                        for class_values in config["lmu_class_warnings"].values():
                            class_values["alert"].update({
                                key: legacy_alert[key] for key in ("enabled", "frequency_hz", "intensity")
                                if key in legacy_alert
                            })
                            class_values["advanced"].update({
                                key: legacy_advanced[key]
                                for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient",
                                            "warning_onset_intercept", "warning_max_intercept", "warning_max_slope")
                                if key in legacy_advanced
                            })
                            old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                            if old_slope > 0:
                                start_value = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                                class_values["advanced"]["warning_max_speed_kmh"] = (100.0 - start_value) / old_slope
                config["game"] = selected
            else:
                # Compatibilité avec l'ancien fichier mono-profil.
                deep_update(config, saved)
                legacy_alert = saved.get("alerts", {}).get("brake_warning", {})
                legacy_advanced = saved.get("advanced", {})
                config["global_brake_warning"]["alert"].update({
                    key: legacy_alert[key] for key in ("enabled", "frequency_hz", "intensity")
                    if key in legacy_alert
                })
                for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient",
                            "warning_onset_intercept", "warning_max_intercept", "warning_max_slope"):
                    if key in legacy_advanced:
                        config["global_brake_warning"]["advanced"][key] = legacy_advanced[key]
                old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                if old_slope > 0:
                    a = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                    config["global_brake_warning"]["advanced"]["warning_max_speed_kmh"] = max(1.0, (100.0-a)/old_slope)
                if str(saved.get("game", "LMU")).upper() == "LMU" and "lmu_class_warnings" not in saved:
                    legacy_alert = saved.get("alerts", {}).get("brake_warning", {})
                    legacy_advanced = saved.get("advanced", {})
                    for class_values in config["lmu_class_warnings"].values():
                        class_values["alert"].update({
                            key: legacy_alert[key] for key in ("enabled", "frequency_hz", "intensity")
                            if key in legacy_alert
                        })
                        class_values["advanced"].update({
                            key: legacy_advanced[key]
                            for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient",
                                        "warning_onset_intercept", "warning_max_intercept", "warning_max_slope")
                            if key in legacy_advanced
                        })
                        old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                        if old_slope > 0:
                            start_value = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                            class_values["advanced"]["warning_max_speed_kmh"] = (100.0 - start_value) / old_slope
                # Migration de l'ancienne valeur par défaut (1.0) vers 0.
                old_advanced = saved.get("advanced", {})
                if old_advanced.get("warning_grip_coefficient") == 1.0:
                    config["advanced"]["warning_grip_coefficient"] = 0.0
        except Exception as exc:
            raise RuntimeError(
                f"Lecture de {CONFIG_PATH.name} impossible : {exc}"
            ) from exc

    game = str(config.get("game", "LMU")).upper()
    if game not in ("AC", "ACC", "ACR", "LMU", "FH6", "IRACING", "F126", "ACEVO", "R3E", "AMS2"):
        raise ValueError(f"Jeu non reconnu dans {CONFIG_PATH.name} : {game}")
    for key in ("lock", "prediction", "brake_warning"):
        hz = int(config["alerts"][key].get("frequency_hz", 40))
        if hz not in ALLOWED_FREQUENCIES:
            raise ValueError(f"Fréquence invalide pour {key}: {hz} Hz")
        config["alerts"][key]["frequency_hz"] = hz
        config["alerts"][key]["intensity"] = max(
            0, min(100, int(config["alerts"][key].get("intensity", 0)))
        )
    config["game"] = game
    config["com_port"] = str(config.get("com_port", "COM7")).strip() or "COM7"
    config["baudrate"] = int(config.get("baudrate", 115200))
    config["send_rate"] = max(1, int(config.get("send_rate", 50)))
    config["read_rate"] = max(1, int(config.get("read_rate", 333)))
    config["udp_port"] = max(1024, min(65535, int(config.get("udp_port", 20444))))
    config["f1_udp_port"] = max(1024, min(65535, int(config.get("f1_udp_port", 20777))))
    # Réglage partagé de l'avertissement préventif pour tous les jeux.
    shared = config.setdefault("global_brake_warning", json.loads(json.dumps(DEFAULT_CONFIG["global_brake_warning"])))
    shared_alert = shared.setdefault("alert", {})
    for key, value in DEFAULT_CONFIG["global_brake_warning"]["alert"].items():
        shared_alert.setdefault(key, value)
    hz = int(shared_alert.get("frequency_hz", 40))
    shared_alert["frequency_hz"] = hz if hz in ALLOWED_FREQUENCIES else 40
    shared_alert["intensity"] = max(0, min(100, int(shared_alert.get("intensity", 20))))
    shared_advanced = shared.setdefault("advanced", {})
    for key, value in DEFAULT_CONFIG["global_brake_warning"]["advanced"].items():
        shared_advanced.setdefault(key, value)
    shared_advanced["warning_max_speed_kmh"] = max(1.0, min(500.0, float(shared_advanced.get("warning_max_speed_kmh", 250.0))))
    shared_advanced["warning_onset_intercept"] = max(0.0, min(100.0, float(shared_advanced.get("warning_onset_intercept", 45.0))))
    # Réglages indépendants de détection et de vibrations pour chaque classe LMU.
    for class_name in DEFAULT_CONFIG["lmu_class_warnings"]:
        entry = config.setdefault("lmu_class_warnings", {}).setdefault(class_name, {})
        class_alerts = entry.setdefault("alerts", {})
        for alert_name in ("lock", "prediction"):
            defaults = DEFAULT_CONFIG["lmu_class_warnings"][class_name]["alerts"][alert_name]
            item = class_alerts.setdefault(alert_name, {})
            for key, value in defaults.items():
                item.setdefault(key, value)
            hz = int(item.get("frequency_hz", defaults["frequency_hz"]))
            item["frequency_hz"] = hz if hz in ALLOWED_FREQUENCIES else defaults["frequency_hz"]
            item["intensity"] = max(0, min(100, int(item.get("intensity", defaults["intensity"]))))
        detection = entry.setdefault("detection", {})
        for key, value in DEFAULT_CONFIG["lmu_class_warnings"][class_name]["detection"].items():
            detection.setdefault(key, value)
        detection["brake_threshold"] = max(0.0, min(1.0, float(detection["brake_threshold"])))
        detection["min_slip_threshold"] = max(0.0, min(10.0, float(detection["min_slip_threshold"])))
        detection["slip_threshold"] = max(detection["min_slip_threshold"], min(10.0, float(detection["slip_threshold"])))
        detection["slip_derivative_threshold"] = max(0.0, float(detection["slip_derivative_threshold"]))
        detection["prediction_horizon_ms"] = max(1, min(250, int(detection["prediction_horizon_ms"])))

    # Validation des réglages d'avertissement indépendants par classe LMU.
    for class_name, defaults in DEFAULT_CONFIG["lmu_class_warnings"].items():
        entry = config.setdefault("lmu_class_warnings", {}).setdefault(class_name, {})
        alert = entry.setdefault("alert", {})
        for key, value in defaults["alert"].items():
            alert.setdefault(key, value)
        hz = int(alert.get("frequency_hz", 40))
        if hz not in ALLOWED_FREQUENCIES:
            hz = 40
        alert["frequency_hz"] = hz
        alert["intensity"] = max(0, min(100, int(alert.get("intensity", 20))))
        advanced_class = entry.setdefault("advanced", {})
        for key, value in defaults["advanced"].items():
            advanced_class.setdefault(key, value)
        advanced_class["warning_max_speed_kmh"] = max(
            1.0, min(500.0, float(advanced_class.get("warning_max_speed_kmh", 250.0))))
        advanced_class["warning_onset_intercept"] = max(
            0.0, min(100.0, float(advanced_class.get("warning_onset_intercept", 45.0))))
    return config


# Trames capturées dans Pit House : 10 à 100 Hz, intensités 0 à 100 %.
# Aucun octet ni checksum n'est généré : on réutilise le module de captures.
from PHF_protocol import get_frame, STOP_FRAME


def moza_frame_for_intensity(intensity, frequency_hz):
    level = max(0, min(100, int(float(intensity) + 0.5)))
    if level == 0:
        return STOP_FRAME
    return get_frame(int(frequency_hz), level)


def compute_progressive_warning(brake_demand, speed_kmh, wheel_slips,
                                advanced, max_intensity, enabled=True,
                                wheel_wear=()):
    """Avertissement préventif avec seuil de début dépendant de la vitesse.

    La pente du seuil de début est calculée automatiquement pour que celui-ci
    atteigne 100 % à warning_max_speed_kmh :
        pente = (100 - A) / vitesse_max
    où A = warning_onset_intercept, exprimé en pourcentage.
    """

    raw_speed = max(0.0, float(speed_kmh))
    if not enabled or raw_speed < float(advanced.get("warning_min_speed_kmh", 0.0)):
        return 0.0

    demand_pct = max(0.0, min(100.0, float(brake_demand) * 100.0))

    max_slip = max(
        (max(0.0, min(1.0, float(value))) for value in wheel_slips),
        default=0.0
    )

    coefficient = max(0.0, min(3.0,
        float(advanced.get("warning_grip_coefficient", 0.0))))

    available_grip = max(0.001, 1.0 - coefficient * max_slip)

    # Santé des pneus : LMU fournit mWear entre 0 et 1.
    # 1 = pneu neuf, 0 = pneu totalement dégradé.
    # Sans télémétrie d'usure, la santé reste à 1.
    tyre_health = min(
        (
            max(0.0, min(1.0, float(value)))
            for value in wheel_wear
            if value is not None
        ),
        default=1.0
    )

    tyre_health = max(0.001, tyre_health)

    effective_speed = raw_speed

    onset_intercept = max(0.0, min(100.0,
        float(advanced.get("warning_onset_intercept", 45.0))))

    max_speed = max(1.0,
        float(advanced.get("warning_max_speed_kmh", 250.0)))

    # Correction par le grip disponible et la santé des pneus.
    # Plus ces deux facteurs diminuent, plus la vitesse effective
    # de référence augmente et plus l'avertissement intervient tôt.
    corrected_max_speed = max_speed / (available_grip * tyre_health)

    onset_slope = (100.0 - onset_intercept) / corrected_max_speed

    onset = onset_intercept + onset_slope * effective_speed

    critical = (
        float(advanced.get("warning_max_intercept", 60.0))
        + float(advanced.get("warning_max_slope", 0.2)) * effective_speed
    )

    if critical <= onset:
        return 0.0

    ratio = (demand_pct - onset) / (critical - onset)
    ratio = max(0.0, min(1.0, ratio))

    return ratio * max(0.0, min(100.0, float(max_intensity)))



SHM_NAME = "Local\\acpmf_physics"


# ============================================================
# ASSETTO CORSA (ORIGINAL) SHARED MEMORY STRUCTURE
# ============================================================

class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4

    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
    ]


AC_PHYSICS_SIZE = ctypes.sizeof(SPageFilePhysics)
ACR_PHYSICS_SIZE = 712


# ============================================================
# LE MANS ULTIMATE - SHARED MEMORY (SDK)
# ============================================================

LMU_SHM_NAME = "LMU_Data"
LMU_HOLD_EVENT = "LMU_Data_HoldEvent"
LMU_DATA_EVENT = "LMU_Data_DataEvent"

LMU_MAP_SIZE = 327680
LMU_TELEMETRY_HEADER_OFFSET = 128464
LMU_TELEM_INFO_SIZE = 1888
LMU_WHEEL_ARRAY_OFFSET = 848
LMU_WHEEL_SIZE = 260
LMU_WHEEL_WEAR_OFFSET = 152  # mWear (double), 0.0 = neuf, 1.0 = usé
LMU_VEHICLE_CLASS_OFFSET = 826  # IP_VehicleClass dans TelemInfoV01 (header SDK, pack=4)
LMU_MAX_VEHICLES = 104

LMU_VEHICLE_CLASSES = {
    0x00: "HYP",
    0x02: "LMP2_ELMS",
    0x03: "LMP2",
    0x04: "LMP3",
    0x05: "GTE",
    0x06: "GT3",
    0x08: "PACE_CAR",
    0xFF: "UNKNOWN",
}

# Le glissement longitudinal au freinage est calculé à partir de la vitesse
# périphérique de la roue et de la vitesse du sol au contact pour les Hypercars,
# LMP2, LMP3 et GTE. Les GT3 restent volontairement en attente.
LMU_SLIP_CLASSES = {0x00, 0x02, 0x03, 0x04, 0x05}

# mGripFract est exploité ici comme indicateur empirique de perte d'adhérence :
# les essais déjà réalisés montrent une baisse vers 0 lors du blocage.
# Le seuil de glissement est chargé depuis moza_settings.json.


# ============================================================
# WINDOWS SHARED MEMORY
# ============================================================

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenFileMappingW.restype = wintypes.HANDLE
kernel32.OpenFileMappingW.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.LPCWSTR,
]

kernel32.MapViewOfFile.restype = wintypes.LPVOID
kernel32.MapViewOfFile.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_size_t,
]

kernel32.UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

# Signatures ANSI utilisées par la mémoire partagée native de LMU.
kernel32.OpenFileMappingA.restype = wintypes.HANDLE
kernel32.OpenFileMappingA.argtypes = [
    wintypes.DWORD, wintypes.BOOL, ctypes.c_char_p
]
kernel32.OpenEventA.restype = wintypes.HANDLE
kernel32.OpenEventA.argtypes = [
    wintypes.DWORD, wintypes.BOOL, ctypes.c_char_p
]
kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]


def connect_shared_memory(size):
    """Open the game's physics shared memory and map the requested size."""
    handle = kernel32.OpenFileMappingW(0x0004, False, SHM_NAME)

    if not handle:
        return None, None

    address = kernel32.MapViewOfFile(handle, 0x0004, 0, 0, size)

    if not address:
        kernel32.CloseHandle(handle)
        return None, None

    return handle, address


def read_ac(address):
    raw = ctypes.string_at(address, AC_PHYSICS_SIZE)
    data = SPageFilePhysics.from_buffer_copy(raw)

    return {
        "packet_id": data.packetId,
        "gas": data.gas,
        "brake": data.brake,
        "speed_kmh": max(0.0, float(data.speedKmh)),
        "wheel_slips": tuple(data.wheelSlip),
    }


def read_acr(address):
    """Read the ACR physics structure (712 bytes)."""
    raw = ctypes.string_at(address, ACR_PHYSICS_SIZE)

    packet_id = struct.unpack_from("<i", raw, 0)[0]
    gas = struct.unpack_from("<f", raw, 4)[0]
    brake = struct.unpack_from("<f", raw, 8)[0]
    # Même disposition initiale que SPageFilePhysics : speedKmh à l'offset 28.
    speed_kmh = struct.unpack_from("<f", raw, 28)[0]
    slip_ratio = struct.unpack_from("<4f", raw, 640)

    # In ACR, slipRatio is positive under acceleration and negative under braking.
    # Keep braking slip only, as a positive magnitude. Acceleration slip becomes 0.
    braking_slips = tuple(max(0.0, -value) for value in slip_ratio)

    return {
        "packet_id": packet_id,
        "gas": gas,
        "brake": brake,
        "speed_kmh": max(0.0, float(speed_kmh)),
        "wheel_slips": braking_slips,
        "slip_ratio": slip_ratio,
    }


def connect_lmu_shared_memory():
    """Ouvre la mémoire partagée native de LMU et ses événements SDK."""
    map_handle = kernel32.OpenFileMappingA(
        0x0004, False, LMU_SHM_NAME.encode("ascii")
    )
    if not map_handle:
        return None, None, None, None

    address = kernel32.MapViewOfFile(
        map_handle, 0x0004, 0, 0, LMU_MAP_SIZE
    )
    if not address:
        kernel32.CloseHandle(map_handle)
        return None, None, None, None

    hold_event = kernel32.OpenEventA(
        0x00100000, False, LMU_HOLD_EVENT.encode("ascii")
    )
    data_event = kernel32.OpenEventA(
        0x00100000, False, LMU_DATA_EVENT.encode("ascii")
    )

    if not hold_event or not data_event:
        if hold_event:
            kernel32.CloseHandle(hold_event)
        if data_event:
            kernel32.CloseHandle(data_event)
        kernel32.UnmapViewOfFile(address)
        kernel32.CloseHandle(map_handle)
        return None, None, None, None

    return map_handle, address, hold_event, data_event


def read_lmu_snapshot(address):
    """
    Lecture diagnostique synchronisée sur les événements de trame LMU.
    Deux copies identiques consécutives sont exigées pour limiter les lectures
    pendant une mise à jour de la mémoire.
    """
    size = 4 + LMU_MAX_VEHICLES * LMU_TELEM_INFO_SIZE
    for _ in range(5):
        first = ctypes.string_at(
            address + LMU_TELEMETRY_HEADER_OFFSET, size
        )
        second = ctypes.string_at(
            address + LMU_TELEMETRY_HEADER_OFFSET, size
        )
        if first == second:
            return first
    return None


def decode_lmu_snapshot(snapshot):
    active = snapshot[0]
    player_idx = snapshot[1]
    player_has_vehicle = bool(snapshot[2])

    if active > LMU_MAX_VEHICLES or player_idx >= LMU_MAX_VEHICLES:
        raise ValueError(
            f"En-tête LMU invalide : activeVehicles={active}, "
            f"playerVehicleIdx={player_idx}, playerHasVehicle={player_has_vehicle}"
        )

    if not player_has_vehicle or player_idx >= active:
        return None

    vehicle = 4 + player_idx * LMU_TELEM_INFO_SIZE
    brake = struct.unpack_from("<d", snapshot, vehicle + 428)[0]
    vehicle_class_id = snapshot[vehicle + LMU_VEHICLE_CLASS_OFFSET]
    vehicle_class = LMU_VEHICLE_CLASSES.get(vehicle_class_id, f"CLASS_{vehicle_class_id:02X}")

    # mLocalVel : vecteur de vitesse locale en m/s.
    vel_x, vel_y, vel_z = struct.unpack_from("<3d", snapshot, vehicle + 184)
    speed_kmh = (vel_x * vel_x + vel_y * vel_y + vel_z * vel_z) ** 0.5 * 3.6

    wheel_slips = []
    grip_fractions = []
    brake_pressures = []
    tire_loads = []
    wheel_rotations = []
    wheel_ground_speeds = []
    wheel_radii = []
    wheel_wear = []

    for i in range(4):
        wheel = vehicle + LMU_WHEEL_ARRAY_OFFSET + i * LMU_WHEEL_SIZE
        brake_pressure = struct.unpack_from("<d", snapshot, wheel + 32)[0]
        rotation = struct.unpack_from("<d", snapshot, wheel + 40)[0]
        ground_velocity = struct.unpack_from("<d", snapshot, wheel + 72)[0]
        tire_load = struct.unpack_from("<d", snapshot, wheel + 104)[0]
        grip_fraction = struct.unpack_from("<d", snapshot, wheel + 112)[0]
        tire_wear = struct.unpack_from("<d", snapshot, wheel + LMU_WHEEL_WEAR_OFFSET)[0]
        radius_cm = snapshot[wheel + 179]
        radius_m = radius_cm / 100.0

        grip_fraction = max(0.0, min(1.0, grip_fraction))
        # LMU : mWear est une fraction d'usure (0 = neuf, 1 = usé).
        # Une valeur hors plage ou non finie est neutralisée.
        if not (tire_wear == tire_wear and abs(tire_wear) != float("inf")):
            tire_wear = 0.0
        tire_wear = max(0.0, min(1.0, tire_wear))
        wheel_wear.append(tire_wear)
        brake_pressures.append(max(0.0, min(1.0, brake_pressure)))
        tire_loads.append(tire_load)
        grip_fractions.append(grip_fraction)
        wheel_rotations.append(rotation)
        wheel_ground_speeds.append(ground_velocity)
        wheel_radii.append(radius_m)

        if vehicle_class_id in LMU_SLIP_CLASSES:
            # mLongitudinalGroundVel est la vitesse du sol au contact.
            # mRotation est en rad/s ; le rayon statique est fourni en cm.
            ground_speed = abs(ground_velocity)
            wheel_speed = abs(rotation) * radius_m
            if ground_speed >= 3.0 and 0.20 <= radius_m <= 0.60:
                slip = max(0.0, min(1.0, (ground_speed - wheel_speed) / ground_speed))
            else:
                slip = 0.0
        else:
            # GT3 et classes non encore prises en charge : pas de faux positif.
            slip = 0.0

        wheel_slips.append(slip)

    if vehicle_class_id in LMU_SLIP_CLASSES:
        detection_method = "WHEEL_SPEED_SLIP"
    elif vehicle_class_id == 0x06:
        detection_method = "GT3_DISABLED"
    else:
        detection_method = "UNSUPPORTED_CLASS"

    return {
        "brake": max(0.0, min(1.0, brake)),
        "speed_kmh": max(0.0, speed_kmh),
        "wheel_slips": tuple(wheel_slips),
        "grip_fractions": tuple(grip_fractions),
        "brake_pressures": tuple(brake_pressures),
        "tire_loads": tuple(tire_loads),
        "wheel_rotations": tuple(wheel_rotations),
        "wheel_ground_speeds": tuple(wheel_ground_speeds),
        "wheel_radii": tuple(wheel_radii),
        "wheel_wear": tuple(wheel_wear),
        "vehicle_class_id": vehicle_class_id,
        "vehicle_class": vehicle_class,
        "detection_method": detection_method,
    }


def read_lmu_frame(address, hold_event, data_event):
    """Retourne les données d'une nouvelle trame ou None si aucune n'est prête."""
    WAIT_OBJECT_0 = 0
    if kernel32.WaitForSingleObject(hold_event, 1) != WAIT_OBJECT_0:
        return None
    if kernel32.WaitForSingleObject(data_event, 1) != WAIT_OBJECT_0:
        return None

    snapshot = read_lmu_snapshot(address)
    if snapshot is None:
        return None
    return decode_lmu_snapshot(snapshot)


# ============================================================
# WHEEL SLIP TRACKING / PREDICTION
# ============================================================

class WheelTracker:
    def __init__(self, history_size=3, slip_threshold=0.3, min_slip_threshold=0.05,
                 prediction_horizon=0.030, slip_derivative_threshold=0.0):
        self.history = deque(maxlen=history_size)
        self.slip_threshold = max(float(min_slip_threshold), float(slip_threshold))
        self.min_slip_threshold = max(0.0, float(min_slip_threshold))
        self.prediction_horizon = prediction_horizon
        self.slip_derivative_threshold = max(0.0, float(slip_derivative_threshold))
        self.slip = 0.0
        self.derivative = 0.0
        self.predicted_time = float("inf")
        self.lock_detected = False
        self.prediction_detected = False

    def update(self, slip):
        now = time.perf_counter()
        self.slip = slip
        self.history.append((now, slip))

        self.derivative = 0.0
        self.predicted_time = float("inf")

        # Calculate derivative over the history window.
        if len(self.history) >= 2:
            t_old, slip_old = self.history[0]
            t_new, slip_new = self.history[-1]
            dt = t_new - t_old

            if dt > 0:
                self.derivative = (slip_new - slip_old) / dt

        # Direct lock / excessive braking-slip detection.
        self.lock_detected = self.slip >= self.min_slip_threshold

        # Predict threshold crossing.
        if self.derivative > 0 and self.derivative >= self.slip_derivative_threshold:
            remaining = self.min_slip_threshold - self.slip
            if remaining > 0:
                self.predicted_time = remaining / self.derivative

        self.prediction_detected = (
            self.slip < self.min_slip_threshold
            and self.predicted_time <= self.prediction_horizon
        )

        return self.lock_detected or self.prediction_detected


class WheelTrackerManager:
    def __init__(self, wheel_count=4, slip_threshold=0.5, min_slip_threshold=0.05,
                 history_size=5, prediction_horizon=0.030, slip_derivative_threshold=0.0):
        self.tracker_settings = {
            "history_size": history_size,
            "slip_threshold": slip_threshold,
            "min_slip_threshold": min_slip_threshold,
            "prediction_horizon": prediction_horizon,
            "slip_derivative_threshold": slip_derivative_threshold,
        }
        self.wheels = [
            WheelTracker(**self.tracker_settings)
            for _ in range(wheel_count)
        ]

    def update(self, wheel_slips):
        while len(self.wheels) < len(wheel_slips):
            self.wheels.append(WheelTracker(**self.tracker_settings))

        return [
            tracker.update(slip)
            for tracker, slip in zip(self.wheels, wheel_slips)
        ]

    def any_lock(self):
        return any(tracker.lock_detected for tracker in self.wheels)

    def any_prediction(self):
        return any(
            tracker.prediction_detected and not tracker.lock_detected
            for tracker in self.wheels
        )

    def any_warning(self):
        return self.any_lock() or self.any_prediction()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    config = load_config()
    game = config["game"]
    alerts = config["alerts"]
    advanced = config["advanced"]
    system_enabled = bool(config.get("system_enabled", True))
    com_port = config["com_port"]
    baudrate = config["baudrate"]
    send_rate = config["send_rate"]
    read_rate = config["read_rate"]
    brake_threshold = float(advanced["brake_threshold"])
    slip_threshold = float(advanced["slip_threshold"])
    min_slip_threshold = float(advanced.get("min_slip_threshold", 0.05))
    slip_derivative_threshold = max(0.0, float(advanced.get("slip_derivative_threshold", 0.0)))
    prediction_horizon = max(0.001, float(advanced["prediction_horizon_ms"]) / 1000.0)

    if game == "FH6":
        physics_size = None
        game_label = "Forza Horizon 6"
    elif game == "F126":
        physics_size = None
        game_label = "F1 26"
    elif game == "IRACING":
        physics_size = None
        game_label = "iRacing"
    elif game == "ACEVO":
        physics_size = None
        game_label = "Assetto Corsa EVO"
    elif game == "R3E":
        physics_size = None
        game_label = "RaceRoom Racing Experience"
    elif game == "AMS2":
        physics_size = None
        game_label = "Automobilista 2"
    elif game == "ACC":
        physics_size = None
        game_label = "Assetto Corsa Competizione"
    elif game == "AC":
        physics_size = AC_PHYSICS_SIZE
        game_label = "Assetto Corsa"
    elif game == "ACR":
        physics_size = ACR_PHYSICS_SIZE
        game_label = "Assetto Corsa Rally"
    else:
        physics_size = None
        game_label = "Le Mans Ultimate"

    print(f"PHF / {game_label} vibration controller")
    print("------------------------------------------")
    print(f"Système de vibrations : {'ACTIF' if system_enabled else 'DÉSACTIVÉ'}")
    print(f"Port série : {com_port} | Envoi : {send_rate} Hz")
    for key, label in (("lock", "Blocage confirmé"),
                       ("prediction", "Prédiction"),
                       ("brake_warning", "Avertissement freinage")):
        item = alerts[key]
        print(f"{label} : {'ON' if item['enabled'] else 'OFF'} | "
              f"{item['frequency_hz']} Hz | {item['intensity']} %")

    ser = None
    game_handle = None
    game_address = None
    lmu_hold_event = None
    lmu_data_event = None
    forza_receiver = None
    f1_receiver = None
    iracing_reader = None
    acevo_reader = None
    raceroom_reader = None
    ams2_reader = None
    acc_reader = None

    current_vibration_intensity = 0.0
    current_vibration_frequency = 40
    current_signal_mode = "OFF"
    current_lmu_method = None
    current_r3e_vehicle = None
    current_ams2_vehicle = None
    wheel_manager = WheelTrackerManager(
        wheel_count=4,
        slip_threshold=slip_threshold,
        min_slip_threshold=min_slip_threshold,
        slip_derivative_threshold=slip_derivative_threshold,
        history_size=5,
        prediction_horizon=prediction_horizon,
    )

    next_read = 0.0
    next_send = 0.0

    try:
        # Conserver l'ordre validé : ouvrir COM7 avec Python avant Pit House.
        ser = serial.Serial(
            com_port,
            baudrate,
            timeout=0.001,
            write_timeout=0.1,
        )
        print(f"PHF connected on {com_port}")

        while True:
            now = time.perf_counter()
            data = None

            # --------------------------------------------
            # Connexion au jeu sélectionné
            # --------------------------------------------
            if game_address is None and now >= next_read:
                try:
                    if game == "FH6":
                        forza_receiver = ForzaUDPReceiver(config.get("udp_port", 20444))
                        game_address = True
                        print("FH6 UDP listening on 0.0.0.0:{}".format(config.get("udp_port", 20444)))
                    elif game == "F126":
                        f1_receiver = F126UDPReceiver(config.get("f1_udp_port", 20777))
                        game_address = True
                        print("F1 26 UDP listening on 0.0.0.0:{} (format 2026)".format(config.get("f1_udp_port", 20777)))
                    elif game == "IRACING":
                        iracing_reader = IRacingTelemetryReader()
                        game_address = True
                        print("iRacing SDK connected (shared memory, 60 Hz).")
                    elif game == "ACEVO":
                        acevo_reader = ACEvoTelemetryReader()
                        game_address = True
                        print("Assetto Corsa EVO physics shared memory connected.")
                    elif game == "R3E":
                        raceroom_reader = RaceRoomTelemetryReader()
                        game_address = True
                        print("RaceRoom shared memory connected (API 3.6+).")
                    elif game == "AMS2":
                        ams2_reader = AMS2TelemetryReader()
                        game_address = True
                        print("Automobilista 2 shared memory connected (Project CARS 2 format).")
                    elif game == "ACC":
                        acc_reader = ACCTelemetryReader()
                        game_address = True
                        print("ACC shared memory connected (physics telemetry, read-only).")
                    elif game == "LMU":
                        (game_handle, game_address,
                         lmu_hold_event, lmu_data_event) = connect_lmu_shared_memory()
                    else:
                        game_handle, game_address = connect_shared_memory(physics_size)
                except Exception as exc:
                    print(f"Waiting for {game_label}: {exc}")
                    if f1_receiver:
                        f1_receiver.close()
                        f1_receiver = None
                    if iracing_reader:
                        iracing_reader.close()
                        iracing_reader = None
                    if acevo_reader:
                        acevo_reader.close()
                        acevo_reader = None
                    if raceroom_reader:
                        raceroom_reader.close()
                        raceroom_reader = None
                    if ams2_reader:
                        ams2_reader.close()
                        ams2_reader = None
                    if forza_receiver:
                        forza_receiver.close()
                        forza_receiver = None
                    game_address = None
                    game_handle = None

                if game_address:
                    print(f"{game_label} connected.")
                else:
                    print(f"Waiting for {game_label}...")

                next_read = now + 1.0

            # --------------------------------------------
            # Lecture télémétrie
            # --------------------------------------------
            if game_address is not None and now >= next_read:
                try:
                    if game == "FH6":
                        data = forza_receiver.read()
                    elif game == "F126":
                        data = f1_receiver.read()
                    elif game == "IRACING":
                        data = iracing_reader.read()
                    elif game == "ACEVO":
                        data = acevo_reader.read()
                        next_read = now + 1.0 / read_rate
                    elif game == "R3E":
                        data = raceroom_reader.read()
                        next_read = now + 1.0 / read_rate
                    elif game == "AMS2":
                        data = ams2_reader.read()
                        next_read = now + 1.0 / min(read_rate, 200)
                    elif game == "ACC":
                        data = acc_reader.read()
                        next_read = now + 1.0 / read_rate
                    elif game == "AC":
                        data = read_ac(game_address)
                    elif game == "ACR":
                        data = read_acr(game_address)
                    else:
                        data = read_lmu_frame(
                            game_address, lmu_hold_event, lmu_data_event
                        )

                    # Les lecteurs UDP sont interrogés au rythme configuré.
                    # iRacing publie à 60 Hz : ne pas retraiter un même buffer.
                    if game == "IRACING":
                        next_read = now + 1.0 / 60.0
                    elif game == "F126":
                        next_read = now + 1.0 / read_rate
                    elif game == "FH6":
                        next_read = now + 1.0 / read_rate

                    # Ne mettre à jour les historiques qu'avec une nouvelle mesure.
                    if data is not None:
                        if game == "AMS2":
                            vehicle_identity = (data.get("vehicle_name", ""), data.get("vehicle_class", ""))
                            if vehicle_identity != current_ams2_vehicle:
                                current_ams2_vehicle = vehicle_identity
                                print(f"AMS2 vehicle: {vehicle_identity[0] or 'Unknown'} | class: {vehicle_identity[1] or 'Unknown'}")
                        if game == "R3E":
                            vehicle_identity = (data.get("vehicle_name", ""), data.get("vehicle_class_id"))
                            if vehicle_identity != current_r3e_vehicle:
                                current_r3e_vehicle = vehicle_identity
                                print(
                                    f"RaceRoom vehicle: {vehicle_identity[0] or 'Unknown'} "
                                    f"| class ID: {vehicle_identity[1]} "
                                    f"| API: {data.get('api_version', '?')}"
                                )
                        if game == "LMU":
                            method = data.get("detection_method", "UNSUPPORTED_CLASS")
                            vehicle_class = data.get("vehicle_class", "UNKNOWN")
                            class_profile = config.get("lmu_class_warnings", {}).get(vehicle_class)
                            detection_cfg = class_profile.get("detection", advanced) if class_profile else advanced
                            active_brake_threshold = float(detection_cfg.get("brake_threshold", brake_threshold))
                            active_slip_threshold = float(detection_cfg.get("slip_threshold", slip_threshold))
                            active_min_slip_threshold = max(0.0, min(active_slip_threshold, float(detection_cfg.get("min_slip_threshold", min_slip_threshold))))
                            active_derivative_threshold = max(0.0, float(detection_cfg.get("slip_derivative_threshold", slip_derivative_threshold)))
                            active_prediction_horizon = max(0.001, float(detection_cfg.get("prediction_horizon_ms", prediction_horizon * 1000.0)) / 1000.0)
                            class_identity = (vehicle_class, method)
                            if class_identity != current_lmu_method:
                                current_lmu_method = class_identity
                                wheel_manager = WheelTrackerManager(
                                    wheel_count=4,
                                    slip_threshold=active_slip_threshold,
                                    min_slip_threshold=active_min_slip_threshold,
                                    slip_derivative_threshold=active_derivative_threshold,
                                    history_size=5,
                                    prediction_horizon=active_prediction_horizon,
                                )
                                print(
                                    f"LMU vehicle class: {vehicle_class} "
                                    f"| detection: {method} "
                                    f"| brake threshold: {active_brake_threshold:.3f} "
                                    f"| slip min/max: {active_min_slip_threshold:.3f}/{active_slip_threshold:.3f}"
                                )
                        else:
                            active_brake_threshold = brake_threshold
                            active_slip_threshold = slip_threshold
                            active_min_slip_threshold = min_slip_threshold
                            class_profile = None

                        wheel_slips = data["wheel_slips"]
                        wheel_manager.update(wheel_slips)

                        confirmed_lock = (
                            data["brake"] > active_brake_threshold
                            and wheel_manager.any_lock()
                        )
                        predicted_lock = (
                            data["brake"] > active_brake_threshold
                            and wheel_manager.any_prediction()
                            and not confirmed_lock
                        )

                        warning_intensity = 0.0
                        # Base commune à tous les jeux ; LMU peut la remplacer
                        # par les réglages spécifiques de la classe reconnue.
                        shared_warning = config["global_brake_warning"]
                        warning_cfg = shared_warning["alert"]
                        warning_advanced = shared_warning["advanced"]
                        if game == "LMU":
                            class_warning = config.get("lmu_class_warnings", {}).get(
                                data.get("vehicle_class", ""))
                            if class_warning is not None:
                                warning_cfg = class_warning["alert"]
                                warning_advanced = class_warning["advanced"]
                        if warning_cfg["enabled"]:
                            warning_intensity = compute_progressive_warning(
                                brake_demand=data["brake"],
                                speed_kmh=data["speed_kmh"],
                                wheel_slips=wheel_slips,
                                advanced=warning_advanced,
                                max_intensity=warning_cfg["intensity"],
                                enabled=system_enabled,
                                wheel_wear=data.get("wheel_wear", ()),
                            )

                        # Les profils LMU remplacent aussi les alertes de blocage/prédiction.
                        active_alerts = class_profile.get("alerts", alerts) if game == "LMU" and class_profile else alerts

                        # Une seule alerte est prioritaire à la fois : confirmé,
                        # puis prédiction, puis avertissement préventif.
                        if (system_enabled and confirmed_lock
                                and active_alerts["lock"]["enabled"]):
                            signal_mode = "LOCK"
                            lock_base_intensity = float(active_alerts["lock"]["intensity"])
                            lock_min_slip = max(
                                0.0,
                                active_min_slip_threshold if game == "LMU" else min_slip_threshold
                            )
                            lock_max_slip = max(
                                lock_min_slip + 0.001,
                                active_slip_threshold if game == "LMU" else slip_threshold
                            )
                            lock_slip = max(wheel_slips, default=0.0)
                            slip_progress = (lock_slip - lock_min_slip) / (lock_max_slip - lock_min_slip)
                            slip_intensity_factor = min(1.0, max(0.001, slip_progress))
                            target_intensity = lock_base_intensity * slip_intensity_factor
                            target_frequency = active_alerts["lock"]["frequency_hz"]
                        elif (system_enabled and predicted_lock
                              and active_alerts["prediction"]["enabled"]):
                            signal_mode = "PREDICTION"
                            target_intensity = active_alerts["prediction"]["intensity"]
                            target_frequency = active_alerts["prediction"]["frequency_hz"]
                        elif system_enabled and warning_intensity > 0.0:
                            signal_mode = "BRAKE_WARNING"
                            target_intensity = warning_intensity
                            target_frequency = warning_cfg["frequency_hz"]
                        else:
                            signal_mode = "OFF"
                            target_intensity = 0.0
                            target_frequency = current_vibration_frequency

                        # Journaliser uniquement les changements de mode,
                        # pas chaque variation de l'intensité progressive.
                        if signal_mode != current_signal_mode:
                            if signal_mode == "LOCK":
                                print(
                                    f"LOCK CONFIRMED | Brake={data['brake']:.2f} | "
                                    f"Slip={max(wheel_slips):.2f} | "
                                    f"Vibration={target_intensity:.0f} %"
                                )
                            elif signal_mode == "PREDICTION":
                                print(
                                    f"LOCK PREDICTION | Brake={data['brake']:.2f} | "
                                    f"Slip={max(wheel_slips):.2f} | "
                                    f"Vibration={target_intensity:.0f} %"
                                )
                            elif signal_mode == "BRAKE_WARNING":
                                print(
                                    f"BRAKE WARNING | Speed={data['speed_kmh']:.1f} km/h | "
                                    f"Brake={data['brake'] * 100:.1f} % | "
                                    f"Vibration={target_intensity:.1f} %"
                                )
                            else:
                                print("All warnings released | Vibration OFF")
                            current_signal_mode = signal_mode

                        if (target_intensity != current_vibration_intensity
                                or target_frequency != current_vibration_frequency):
                            previous_intensity = current_vibration_intensity
                            current_vibration_intensity = target_intensity
                            current_vibration_frequency = target_frequency
                            next_send = 0.0
                            # Envoyer explicitement la trame STOP à la libération.
                            if previous_intensity > 0 and target_intensity <= 0:
                                ser.write(STOP_FRAME)

                        # Fréquence de lecture :
                        # AC/ACR 333 Hz ; LMU attend ses événements de trame.
                        if game == "LMU":
                            next_read = now + 0.001
                        elif game == "IRACING":
                            next_read = now + 1.0 / 60.0
                        else:
                            next_read = now + 1.0 / read_rate

                except Exception as e:
                    print(f"{game_label} connection lost:", e)

                    if current_vibration_intensity > 0:
                        try:
                            ser.write(STOP_FRAME)
                        except Exception:
                            pass

                    current_vibration_intensity = 0.0
                    current_signal_mode = "OFF"

                    if game == "FH6" and forza_receiver:
                        forza_receiver.close()
                        forza_receiver = None
                    if game == "F126" and f1_receiver:
                        f1_receiver.close()
                        f1_receiver = None
                    if game == "IRACING" and iracing_reader:
                        iracing_reader.close()
                        iracing_reader = None
                    if game == "ACEVO" and acevo_reader:
                        acevo_reader.close()
                        acevo_reader = None
                    if game == "R3E" and raceroom_reader:
                        raceroom_reader.close()
                        raceroom_reader = None
                    if game == "AMS2" and ams2_reader:
                        ams2_reader.close()
                        ams2_reader = None
                    if game == "ACC" and acc_reader:
                        acc_reader.close()
                        acc_reader = None
                    if game == "LMU":
                        for handle in (lmu_hold_event, lmu_data_event):
                            if handle:
                                kernel32.CloseHandle(handle)
                        lmu_hold_event = None
                        lmu_data_event = None

                    if game_address and game not in ("FH6", "F126", "IRACING", "ACEVO", "R3E", "AMS2", "ACC"):
                        kernel32.UnmapViewOfFile(game_address)
                    if game_handle:
                        kernel32.CloseHandle(game_handle)

                    game_address = None
                    game_handle = None
                    next_read = now + 1.0

            # --------------------------------------------
            # Rafraîchissement de la commande PHF
            # --------------------------------------------
            if current_vibration_intensity > 0 and now >= next_send:
                ser.write(moza_frame_for_intensity(
                    current_vibration_intensity, current_vibration_frequency
                ))
                next_send = now + 1.0 / send_rate

            # Vider le buffer de réception.
            if ser.in_waiting:
                ser.read(ser.in_waiting)

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nStopping program...")

    finally:
        if ser and ser.is_open:
            try:
                ser.write(STOP_FRAME)
                time.sleep(0.1)
                ser.close()
            except Exception:
                pass

        if forza_receiver:
            forza_receiver.close()
        if f1_receiver:
            f1_receiver.close()
        if iracing_reader:
            iracing_reader.close()
        if acevo_reader:
            acevo_reader.close()
        if raceroom_reader:
            raceroom_reader.close()
        if ams2_reader:
            ams2_reader.close()
        if acc_reader:
            acc_reader.close()

        for handle in (lmu_hold_event, lmu_data_event):
            if handle:
                kernel32.CloseHandle(handle)

        if game_address and game not in ("FH6", "F126", "IRACING", "ACEVO", "R3E", "AMS2", "ACC"):
            kernel32.UnmapViewOfFile(game_address)

        if game_handle:
            kernel32.CloseHandle(game_handle)

        print("Program stopped.")


if __name__ == "__main__":
    main()
