import json
import sys
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QTabWidget, QLabel, QComboBox, QCheckBox, QSlider,
    QSpinBox, QPushButton, QGroupBox, QMessageBox, QLineEdit,
    QStatusBar, QFrame, QScrollArea
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "EPPHF_settings.json"

FREQUENCIES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

DEFAULT_CONFIG = {
    "game": "LMU",
    "udp_port": 20444,
    "f1_udp_port": 20777,
    "com_port": "COM7",
    "baudrate": 115200,
    "system_enabled": True,
    "send_rate": 50,
    "read_rate": 333,
    "alerts": {
        "lock": {"enabled": True, "frequency_hz": 40, "intensity": 50},
        "prediction": {"enabled": True, "frequency_hz": 40, "intensity": 40},
        "brake_warning": {"enabled": True, "frequency_hz": 40, "intensity": 20}
    },
    "advanced": {
        "brake_threshold": 0.05,
        "slip_threshold": 0.5,
        "slip_derivative_threshold": 0.0,
        "prediction_horizon_ms": 30,
        "warning_min_speed_kmh": 0.0,
        "warning_onset_intercept": 45.0,
        "warning_max_speed_kmh": 250.0,
        "warning_max_intercept": 60.0,
        "warning_max_slope": 40.0 / 200.0
    },
    "lmu_class_warnings": {
        "HYP": {
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
}
}

STYLE = """
QMainWindow, QWidget { background: #171a21; color: #e8eaf0; font-size: 10pt; }
QTabWidget::pane { border: 1px solid #343a46; border-radius: 8px; }
QTabBar::tab { background: #222733; padding: 10px 18px; margin: 3px; border-radius: 6px; }
QTabBar::tab:selected { background: #365b86; }
QGroupBox { border: 1px solid #394252; border-radius: 8px; margin-top: 12px; padding: 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QComboBox, QSpinBox, QLineEdit { background: #252b36; border: 1px solid #454e5e; border-radius: 5px; padding: 6px; min-height: 22px; }
QPushButton { background: #315f91; border: 0; border-radius: 6px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #3e75ae; }
QPushButton:disabled { background: #3a3f49; color: #9298a3; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 6px; background: #343c49; border-radius: 3px; }
QSlider::handle:horizontal { background: #6aa5e8; width: 16px; margin: -5px 0; border-radius: 8px; }
QStatusBar { background: #11141a; color: #aeb6c4; }
"""

class LMUClassWarningEditor(QGroupBox):
    """Independent predictive warning settings for an LMU class."""
    def __init__(self, class_name, title, parent=None):
        super().__init__(title, parent)
        self.class_name = class_name
        form = QFormLayout(self)
        self.enabled = QCheckBox("Activer l’avertissement prédictif")
        self.frequency = QComboBox()
        for hz in FREQUENCIES:
            self.frequency.addItem(f"{hz} Hz", hz)
        self.intensity = QSlider(Qt.Horizontal)
        self.intensity.setRange(0, 100)
        self.intensity_value = QLabel("20 %")
        self.intensity_value.setMinimumWidth(48)
        self.intensity.valueChanged.connect(
            lambda value: self.intensity_value.setText(f"{value} %"))
        row = QHBoxLayout()
        row.addWidget(self.intensity, 1)
        row.addWidget(self.intensity_value)
        form.addRow(self.enabled)
        form.addRow("Fréquence", self.frequency)
        form.addRow("Intensité maximale", row)

        curve = QGroupBox("Courbe d’avertissement")
        curve_form = QFormLayout(curve)
        self.min_speed = QDoubleSpinBoxCompat(0, 500, 1, 0)
        self.min_speed.setSuffix(" km/h")
        self.grip_coefficient = QDoubleSpinBoxCompat(0, 500, 0.01, 2)
        self.grip_coefficient.setSuffix(" ×")
        self.wear_coefficient = QDoubleSpinBoxCompat(0, 100, 0.01, 2)
        self.wear_coefficient.setSuffix(" ×")
        self.wear_coefficient.setToolTip("S’applique uniquement si le jeu fournit une usure exploitable pour chaque pneu. 0 désactive cet effet.")
        self.onset_intercept = QDoubleSpinBoxCompat(0, 100, 0.5, 1)
        self.onset_intercept.setSuffix(" %")
        self.max_speed = QDoubleSpinBoxCompat(1, 5000, 5, 0)
        self.max_speed.setSuffix(" km/h")
        self.max_intercept = QDoubleSpinBoxCompat(0, 2000, 0.5, 1)
        self.max_intercept.setSuffix(" %")
        self.max_slope = QDoubleSpinBoxCompat(0, 20, 0.005, 3)
        self.max_slope.setSuffix(" % / km/h")
        curve_form.addRow("Vitesse minimale d’activation", self.min_speed)
        curve_form.addRow("Influence du glissement sur l’adhérence disponible", self.grip_coefficient)
        curve_form.addRow("Influence de l’usure des pneus", self.wear_coefficient)
        curve_form.addRow("Départ : valeur à 0 km/h (A)", self.onset_intercept)
        curve_form.addRow("Vitesse maximale sans avertissement", self.max_speed)
        curve_form.addRow("Maximum : valeur à 0 km/h", self.max_intercept)
        curve_form.addRow("Maximum : pente (% par km/h)", self.max_slope)
        note = QLabel(
            "La pente du seuil de départ est calculée automatiquement : "
            "(100 − A) / vitesse maximale. À cette vitesse, le seuil atteint 100 % de freinage."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#aeb8c8; padding:6px;")
        curve_form.addRow(note)
        outer = QVBoxLayout()
        outer.addWidget(curve)

        detection_group = QGroupBox("Détection et prédiction du blocage")
        detection_form = QFormLayout(detection_group)
        self.brake_threshold = QDoubleSpinBoxCompat(0, 1, 0.01, 3)
        self.min_slip_threshold = QDoubleSpinBoxCompat(0, 10, 0.001, 3)
        self.slip_threshold = QDoubleSpinBoxCompat(0, 10, 0.001, 3)
        self.slip_derivative_threshold = QDoubleSpinBoxCompat(0, 1000, 0.001, 2)
        self.slip_derivative_threshold.setSuffix(" /s")
        self.prediction_horizon = QSpinBox()
        self.prediction_horizon.setRange(1, 250)
        self.prediction_horizon.setSuffix(" ms")
        detection_form.addRow("Seuil minimal de freinage", self.brake_threshold)
        detection_form.addRow("Glissement minimal (détection)", self.min_slip_threshold)
        detection_form.addRow("Glissement maximal (échelle intensité)", self.slip_threshold)
        detection_form.addRow("Seuil de dérivée du glissement", self.slip_derivative_threshold)
        detection_form.addRow("Horizon de prédiction", self.prediction_horizon)
        outer.addWidget(detection_group)

        self.class_alert_widgets = {}
        for alert_key, title_text, defaults in (
            ("lock", "Blocage confirmé", (50, 40)),
            ("prediction", "Prédiction du blocage", (40, 40)),
        ):
            alert_group = QGroupBox(f"Vibration — {title_text}")
            alert_form = QFormLayout(alert_group)
            enabled_widget = QCheckBox("Activer cette vibration")
            frequency_widget = QComboBox()
            for hz_value in FREQUENCIES:
                frequency_widget.addItem(f"{hz_value} Hz", hz_value)
            intensity_widget = QSlider(Qt.Horizontal)
            intensity_widget.setRange(0, 100)
            intensity_label = QLabel(f"{defaults[0]} %")
            intensity_widget.valueChanged.connect(
                lambda value, label=intensity_label: label.setText(f"{value} %"))
            intensity_row = QHBoxLayout()
            intensity_row.addWidget(intensity_widget, 1)
            intensity_row.addWidget(intensity_label)
            alert_form.addRow(enabled_widget)
            alert_form.addRow("Fréquence", frequency_widget)
            alert_form.addRow("Intensité", intensity_row)
            outer.addWidget(alert_group)
            self.class_alert_widgets[alert_key] = (enabled_widget, frequency_widget, intensity_widget)

        form.addRow(outer)

    def load(self, values):
        alert = values.get("alert", {})
        advanced = values.get("advanced", {})
        self.enabled.setChecked(bool(alert.get("enabled", True)))
        hz = int(alert.get("frequency_hz", 40))
        idx = self.frequency.findData(hz)
        self.frequency.setCurrentIndex(idx if idx >= 0 else self.frequency.findData(40))
        self.intensity.setValue(int(alert.get("intensity", 20)))
        self.min_speed.setValue(float(advanced.get("warning_min_speed_kmh", 0)))
        self.grip_coefficient.setValue(float(advanced.get("warning_grip_coefficient", 0)))
        self.wear_coefficient.setValue(float(advanced.get("warning_wear_coefficient", 0)))
        self.onset_intercept.setValue(float(advanced.get("warning_onset_intercept", 45)))
        self.max_speed.setValue(float(advanced.get("warning_max_speed_kmh", 250)))
        self.max_intercept.setValue(float(advanced.get("warning_max_intercept", 60)))
        self.max_slope.setValue(float(advanced.get("warning_max_slope", 0.2)))

        detection = values.get("detection", {})
        self.brake_threshold.setValue(float(detection.get("brake_threshold", 0.05)))
        self.min_slip_threshold.setValue(float(detection.get("min_slip_threshold", 0.05)))
        self.slip_threshold.setValue(float(detection.get("slip_threshold", 0.5)))
        self.slip_derivative_threshold.setValue(float(detection.get("slip_derivative_threshold", 0.0)))
        self.prediction_horizon.setValue(int(detection.get("prediction_horizon_ms", 30)))
        class_alerts = values.get("alerts", {})
        for alert_key, widgets in self.class_alert_widgets.items():
            enabled_widget, frequency_widget, intensity_widget = widgets
            alert_values = class_alerts.get(alert_key, {})
            enabled_widget.setChecked(bool(alert_values.get("enabled", True)))
            idx = frequency_widget.findData(int(alert_values.get("frequency_hz", 40)))
            frequency_widget.setCurrentIndex(idx if idx >= 0 else frequency_widget.findData(40))
            intensity_widget.setValue(int(alert_values.get("intensity", 50 if alert_key == "lock" else 40)))

    def export(self):
        return {
            "alert": {
                "enabled": self.enabled.isChecked(),
                "frequency_hz": int(self.frequency.currentData()),
                "intensity": self.intensity.value(),
            },
            "detection": {
                "brake_threshold": self.brake_threshold.value(),
                "min_slip_threshold": self.min_slip_threshold.value(),
                "slip_threshold": self.slip_threshold.value(),
                "slip_derivative_threshold": self.slip_derivative_threshold.value(),
                "prediction_horizon_ms": self.prediction_horizon.value(),
            },
            "alerts": {
                key: {
                    "enabled": widgets[0].isChecked(),
                    "frequency_hz": int(widgets[1].currentData()),
                    "intensity": widgets[2].value(),
                }
                for key, widgets in self.class_alert_widgets.items()
            },
            "advanced": {
                "warning_min_speed_kmh": self.min_speed.value(),
                "warning_grip_coefficient": self.grip_coefficient.value(),
                "warning_wear_coefficient": self.wear_coefficient.value(),
                "warning_onset_intercept": self.onset_intercept.value(),
                "warning_max_speed_kmh": self.max_speed.value(),
                "warning_max_intercept": self.max_intercept.value(),
                "warning_max_slope": self.max_slope.value(),
            },
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evgueni Active Pedal — Configuration")
        self.resize(820, 720)
        self.test_serial = None
        self.test_timer = QTimer(self)
        self.test_timer.setSingleShot(True)
        self.test_timer.timeout.connect(self.stop_test)

        # Charger les profils avant de construire les onglets.
        self.profiles, selected_game, self.global_brake_warning = self.load_profiles()
        self._loading_profile = True
        self._active_game = selected_game
        self.config = self.profile_config(selected_game)

        tabs = QTabWidget()
        tabs.addTab(self.build_general_tab(), "Général")
        tabs.addTab(self.build_advanced_tab(), "Avancé")
        tabs.addTab(self.build_test_tab(), "Test")
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(tabs)
        bottom_buttons = QHBoxLayout()

        self.save_button = QPushButton("Enregistrer les paramètres")
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setMinimumHeight(46)

        self.launch_button = QPushButton("Lancer le contrôleur PHF")
        self.launch_button.clicked.connect(self.launch_controller)
        self.launch_button.setMinimumHeight(46)
        self.launch_button.setStyleSheet(
            "QPushButton { background: #27845a; }"
            "QPushButton:hover { background: #329b6b; }"
        )

        bottom_buttons.addWidget(self.save_button, 1)
        bottom_buttons.addWidget(self.launch_button, 1)
        central_layout.addLayout(bottom_buttons)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(f"Configuration : {CONFIG_PATH.name}")
        self.setStyleSheet(STYLE)
        selected_index = self.game.findData(selected_game)
        if selected_index >= 0:
            self.game.setCurrentIndex(selected_index)
        self.apply_config_to_widgets()
        self.global_warning_editor.load(self.global_brake_warning)
        self._loading_profile = False
        self.game.currentTextChanged.connect(self.change_game_profile)

    def profile_config(self, game):
        config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.deep_update(config, self.profiles.get(game, {}))
        config["game"] = game
        return config

    def load_profiles(self):
        profiles = {name: json.loads(json.dumps(DEFAULT_CONFIG))
                    for name in ("LMU", "AC", "ACC", "ACR", "FH6", "IRACING", "F126", "ACEVO", "R3E", "AMS2")}
        selected = "LMU"
        shared_warning = {
            "alert": {"enabled": True, "frequency_hz": 40, "intensity": 20},
            "advanced": {"warning_min_speed_kmh": 0.0, "warning_grip_coefficient": 0.0,
                        "warning_wear_coefficient": 0.0,
                         "warning_onset_intercept": 45.0, "warning_max_speed_kmh": 250.0,
                         "warning_max_intercept": 60.0, "warning_max_slope": 0.2}
        }
        if not CONFIG_PATH.exists():
            return profiles, selected, shared_warning
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and isinstance(saved.get("profiles"), dict):
                selected = str(saved.get("selected_game", "LMU")).upper()
                if isinstance(saved.get("global_brake_warning"), dict):
                    self.deep_update(shared_warning, saved["global_brake_warning"])
                else:
                    legacy_profile = saved.get("profiles", {}).get(selected, {})
                    legacy_alert = legacy_profile.get("alerts", {}).get("brake_warning", {})
                    legacy_advanced = legacy_profile.get("advanced", {})
                    shared_warning["alert"].update({k: legacy_alert[k] for k in ("enabled", "frequency_hz", "intensity") if k in legacy_alert})
                    for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient", "warning_onset_intercept", "warning_max_intercept", "warning_max_slope"):
                        if key in legacy_advanced: shared_warning["advanced"][key] = legacy_advanced[key]
                    old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                    if old_slope > 0:
                        a = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                        shared_warning["advanced"]["warning_max_speed_kmh"] = max(1.0, (100.0-a)/old_slope)
                for name in profiles:
                    if isinstance(saved["profiles"].get(name), dict):
                        saved_profile = saved["profiles"][name]
                        self.deep_update(profiles[name], saved_profile)
                        if name == "LMU" and "lmu_class_warnings" not in saved_profile:
                            legacy_alert = saved_profile.get("alerts", {}).get("brake_warning", {})
                            legacy_advanced = saved_profile.get("advanced", {})
                            for class_values in profiles[name]["lmu_class_warnings"].values():
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
            else:
                # Migration de l'ancien fichier mono-profil : on conserve ses
                # réglages dans le jeu précédemment sélectionné.
                selected = str(saved.get("game", "LMU")).upper()
                if selected not in profiles:
                    selected = "LMU"
                self.deep_update(profiles[selected], saved)
                legacy_alert = saved.get("alerts", {}).get("brake_warning", {})
                legacy_advanced = saved.get("advanced", {})
                shared_warning["alert"].update({k: legacy_alert[k] for k in ("enabled", "frequency_hz", "intensity") if k in legacy_alert})
                for key in ("warning_min_speed_kmh", "warning_grip_coefficient", "warning_wear_coefficient", "warning_onset_intercept", "warning_max_intercept", "warning_max_slope"):
                    if key in legacy_advanced: shared_warning["advanced"][key] = legacy_advanced[key]
                old_slope = float(legacy_advanced.get("warning_onset_slope", 0.0))
                if old_slope > 0:
                    a = float(legacy_advanced.get("warning_onset_intercept", 45.0))
                    shared_warning["advanced"]["warning_max_speed_kmh"] = max(1.0, (100.0-a)/old_slope)
                if selected == "LMU" and "lmu_class_warnings" not in saved:
                    legacy_alert = saved.get("alerts", {}).get("brake_warning", {})
                    legacy_advanced = saved.get("advanced", {})
                    for class_values in profiles[selected]["lmu_class_warnings"].values():
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
                # L'ancien coefficient avait 1.0 comme valeur par défaut.
                # On migre cette ancienne valeur par défaut vers la nouvelle (0).
                old_advanced = saved.get("advanced", {})
                if old_advanced.get("warning_grip_coefficient") == 1.0:
                    profiles[selected]["advanced"]["warning_grip_coefficient"] = 0.0
        except Exception as exc:
            QMessageBox.warning(self, "Configuration",
                                f"Impossible de lire le fichier JSON : {exc}")
        if selected not in profiles:
            selected = "LMU"
        return profiles, selected, shared_warning

    @staticmethod
    def deep_update(base, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                MainWindow.deep_update(base[key], value)
            else:
                base[key] = value

    def build_general_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        group = QGroupBox("Application")
        form = QFormLayout(group)
        self.game = QComboBox()
        for label, key in (("LMU", "LMU"), ("Assetto Corsa", "AC"),
                           ("Assetto Corsa Competizione", "ACC"),
                           ("Assetto Corsa Rally", "ACR"), ("Forza Horizon 6", "FH6"),
                           ("iRacing", "IRACING"), ("F1 26", "F126"),
                           ("Assetto Corsa EVO", "ACEVO"),
                           ("RaceRoom Racing Experience", "R3E"),
                           ("Automobilista 2", "AMS2")):
            self.game.addItem(label, key)
        self.game.insertSeparator(self.game.count())
        planned_games = []
        for game_name in planned_games:
            self.game.addItem(game_name)
            item = self.game.model().item(self.game.count() - 1)
            if item is not None:
                item.setFlags(Qt.NoItemFlags)
        self.com_port = QLineEdit()
        self.udp_port = QSpinBox()
        self.udp_port.setRange(1024, 65535)
        self.udp_port.setValue(20444)
        self.f1_udp_port = QSpinBox()
        self.f1_udp_port.setRange(1024, 65535)
        self.f1_udp_port.setValue(20777)
        self.system_enabled = QCheckBox("Activer le retour haptique")
        self.send_rate = QSpinBox()
        self.send_rate.setRange(1, 200)
        self.send_rate.setSuffix(" Hz")
        self.read_rate = QSpinBox()
        self.read_rate.setRange(1, 1000)
        self.read_rate.setSuffix(" Hz")
        form.addRow("Jeu sélectionné", self.game)
        game_info = QLabel(
            "Lecteurs télémétriques disponibles : LMU, Assetto Corsa, Assetto Corsa Competizione, Assetto Corsa Rally, "
            "Forza Horizon 6, iRacing, F1 26, Assetto Corsa EVO, RaceRoom et Automobilista 2."
        )
        game_info.setWordWrap(True)
        form.addRow(game_info)
        form.addRow("Port série PHF", self.com_port)
        form.addRow("Port UDP FH6 (Data Out)", self.udp_port)
        form.addRow("Port UDP F1 26", self.f1_udp_port)
        form.addRow(self.system_enabled)
        form.addRow("Fréquence d’envoi", self.send_rate)
        form.addRow("Fréquence de lecture télémétrique AC / ACC / ACR / FH6 / F1 26 / AC EVO / RaceRoom / AMS2 (200 Hz max. pour AMS2)", self.read_rate)
        layout.addWidget(group)
        info = QLabel(
            "Les paramètres enregistrés sont chargés au démarrage du programme principal : "
            "PHF_controller.py. Après toute modification, cliquez sur « Enregistrer les paramètres »."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aeb8c8; padding:10px;")
        layout.addWidget(info)
        layout.addStretch()
        return page

    def build_advanced_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        global_group = QGroupBox("Avertissement prédictif — paramètres généraux (tous les jeux)")
        global_layout = QVBoxLayout(global_group)
        self.global_warning_editor = LMUClassWarningEditor(
            "GLOBAL", "Paramètres généraux de l’avertissement prédictif")
        global_layout.addWidget(self.global_warning_editor)
        global_note = QLabel(
            "Ces paramètres sont communs à AC, ACR et FH6, et servent de référence pour LMU. "
            "Lorsqu’une catégorie LMU est détectée et possède ses propres paramètres, ceux-ci remplacent les valeurs générales. "
            "Une catégorie inconnue utilise les paramètres généraux."
        )
        global_note.setWordWrap(True)
        global_note.setStyleSheet("color:#aeb8c8; padding:6px;")
        global_layout.addWidget(global_note)
        layout.addWidget(global_group)

        class_group = QGroupBox("Catégories LMU — remplacement des paramètres généraux")
        class_layout = QVBoxLayout(class_group)
        self.lmu_class_tabs = QTabWidget()
        self.lmu_class_editors = {}
        class_titles = {
            "HYP": "Hypercar",
            "LMP2_ELMS": "LMP2 ELMS",
            "LMP2": "LMP2",
            "LMP3": "LMP3",
            "GTE": "GTE",
            "GT3": "GT3",
        }
        for class_name, title in class_titles.items():
            editor = LMUClassWarningEditor(class_name, f"Avertissement — {title}")
            self.lmu_class_editors[class_name] = editor
            self.lmu_class_tabs.addTab(editor, title)
        class_layout.addWidget(self.lmu_class_tabs)
        class_note = QLabel(
            "Pour une catégorie LMU détectée, ces paramètres remplacent entièrement les paramètres généraux : "
            "activation, fréquence, intensité et courbe. Cela permet à la catégorie GT3 de conserver son avertissement prédictif "
            "même lorsque son détecteur de blocage de roue est désactivé."
        )
        class_note.setWordWrap(True)
        class_note.setStyleSheet("color:#aeb8c8; padding:6px;")
        class_layout.addWidget(class_note)
        layout.addWidget(class_group)
        layout.addStretch()

        # L'onglet Advanced contient plusieurs groupes et des sous-onglets LMU.
        # Le contenu défile verticalement lorsque la hauteur de fenêtre est insuffisante.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    def build_test_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        group = QGroupBox("Vibration manuelle")
        form = QFormLayout(group)
        self.test_frequency = QComboBox()
        for hz in FREQUENCIES:
            self.test_frequency.addItem(f"{hz} Hz", hz)
        self.test_intensity = QSpinBox()
        self.test_intensity.setRange(0, 100)
        self.test_intensity.setSuffix(" %")
        self.test_duration = QSpinBox()
        self.test_duration.setRange(100, 5000)
        self.test_duration.setSingleStep(100)
        self.test_duration.setValue(500)
        self.test_duration.setSuffix(" ms")
        self.test_port = QLineEdit()
        form.addRow("Fréquence", self.test_frequency)
        form.addRow("Intensité", self.test_intensity)
        form.addRow("Durée", self.test_duration)
        form.addRow("Port COM", self.test_port)
        layout.addWidget(group)
        self.test_button = QPushButton("Envoyer une vibration de test")
        self.test_button.clicked.connect(self.start_test)
        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet("background:#9d3f46;")
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)
        buttons = QHBoxLayout()
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.stop_button)
        layout.addLayout(buttons)
        note = QLabel(
            "Le test matériel nécessite pyserial et le module PHF_protocol.py "
            "dans le même dossier. Les fréquences proposées disposent de trames capturées "
            "pour des intensités de 0 à 100 %."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#aeb8c8; padding:10px;")
        layout.addWidget(note)
        layout.addStretch()
        return page

    def apply_config_to_widgets(self):
        c = self.config
        game_index = self.game.findData(c.get("game", "LMU"))
        if game_index >= 0:
            self.game.setCurrentIndex(game_index)
        self.com_port.setText(c.get("com_port", "COM7"))
        self.udp_port.setValue(int(c.get("udp_port", 20444)))
        self.f1_udp_port.setValue(int(c.get("f1_udp_port", 20777)))
        self.test_port.setText(c.get("com_port", "COM7"))
        self.system_enabled.setChecked(c.get("system_enabled", True))
        self.send_rate.setValue(int(c.get("send_rate", 50)))
        self.read_rate.setValue(int(c.get("read_rate", 333)))
        a = c["advanced"]
        for class_name, editor in self.lmu_class_editors.items():
            values = c.get("lmu_class_warnings", {}).get(class_name, {})
            editor.load(values)

    def collect_config(self):
        # Conserver les anciens champs communs pour compatibilité avec les profils
        # existants ; les avertissements LMU utilisent désormais l'édition par classe.
        a = self.config.get("advanced", {})
        return {
            "game": self.game.currentData() or self.game.currentText(),
            "com_port": self.com_port.text().strip() or "COM7",
            "udp_port": self.udp_port.value(),
            "f1_udp_port": self.f1_udp_port.value(),
            "baudrate": 115200,
            "system_enabled": self.system_enabled.isChecked(),
            "send_rate": self.send_rate.value(),
            "read_rate": self.read_rate.value(),
            # Les anciennes alertes et les anciens seuils globaux sont conservés
            # dans le JSON pour compatibilité, mais ne sont plus éditables ici.
            "alerts": self.config.get("alerts", DEFAULT_CONFIG["alerts"]),
            "advanced": dict(a),
            "lmu_class_warnings": {
                class_name: editor.export()
                for class_name, editor in self.lmu_class_editors.items()
            }
        }

    def change_game_profile(self, game):
        if getattr(self, "_loading_profile", False):
            return
        game = self.game.currentData() or game
        previous_game = getattr(self, "_active_game", None)
        if previous_game:
            self.profiles[previous_game] = self.collect_config()
        self._active_game = game
        self.config = self.profile_config(game)
        self._loading_profile = True
        self.apply_config_to_widgets()
        self._loading_profile = False
        self.statusBar().showMessage(f"Profil chargé : {game}", 4000)

    def save_config(self):
        active_game = self.game.currentData() or self.game.currentText()
        self.profiles[active_game] = self.collect_config()
        self.global_brake_warning = self.global_warning_editor.export()
        try:
            payload = {
                "selected_game": active_game,
                "profiles": self.profiles,
                "global_brake_warning": self.global_brake_warning,
            }
            CONFIG_PATH.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            self.statusBar().showMessage(
                f"Paramètres enregistrés dans {CONFIG_PATH.name}", 5000
            )
            return True
        except Exception as exc:
            QMessageBox.critical(
                self, "Échec de l’enregistrement",
                f"Impossible d’écrire {CONFIG_PATH.name} :\n{exc}"
            )
            return False

    def launch_controller(self):
        controller_path = APP_DIR / "PHF_controller.py"

        if not controller_path.is_file():
            QMessageBox.critical(
                self,
                "Contrôleur introuvable",
                f"Impossible de trouver PHF_controller.py dans :\n{APP_DIR}"
            )
            return

        # Enregistrer les réglages avant tout redémarrage.
        if not self.save_config():
            return

        process = getattr(self, "_controller_process", None)
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
                self.statusBar().showMessage(
                    "Contrôleur PHF arrêté ; redémarrage...", 3000
                )
            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "Impossible d’arrêter le contrôleur",
                    f"Le contrôleur n’a pas pu être arrêté :\n{exc}"
                )
                return

        try:
            # Si l’interface a été lancée avec pythonw.exe, utiliser python.exe
            # afin que la console du contrôleur reste visible sous Windows.
            python_exe = Path(sys.executable)
            if sys.platform == "win32" and python_exe.name.lower() == "pythonw.exe":
                console_python = python_exe.with_name("python.exe")
                if console_python.is_file():
                    python_exe = console_python

            creation_flags = (
                subprocess.CREATE_NEW_CONSOLE
                if sys.platform == "win32" else 0
            )
            self._controller_process = subprocess.Popen(
                [str(python_exe), str(controller_path)],
                cwd=str(APP_DIR),
                creationflags=creation_flags
            )
            self.statusBar().showMessage(
                "Contrôleur PHF lancé", 5000
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Impossible de lancer le contrôleur",
                str(exc)
            )

    def start_test(self):
        if self.test_serial is not None:
            return
        hz = int(self.test_frequency.currentData())
        intensity = self.test_intensity.value()
        if intensity <= 0:
            QMessageBox.information(self, "Test PHF", "Choisissez une intensité supérieure à 0 %.")
            return
        try:
            from PHF_protocol import get_frame
            import serial
            frame = get_frame(hz, intensity)
            self.test_serial = serial.Serial(
                self.test_port.text().strip() or "COM7",
                115200, timeout=0.1, write_timeout=0.2
            )
            self.test_serial.write(frame)
            self.test_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.test_timer.start(self.test_duration.value())
            self.statusBar().showMessage(f"Test en cours : {hz} Hz — {intensity} %")
        except Exception as exc:
            self.stop_test()
            QMessageBox.critical(self, "Échec du test", str(exc))

    def stop_test(self):
        self.test_timer.stop()
        if self.test_serial is not None:
            try:
                from PHF_protocol import STOP_FRAME
                self.test_serial.write(STOP_FRAME)
                self.test_serial.close()
            except Exception:
                pass
            self.test_serial = None
        if hasattr(self, "test_button"):
            self.test_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        if self.statusBar():
            self.statusBar().showMessage("Vibration arrêtée", 3000)

    def closeEvent(self, event):
        self.stop_test()
        event.accept()


# Small local helper keeps the main code readable.
from PySide6.QtWidgets import QDoubleSpinBox
class QDoubleSpinBoxCompat(QDoubleSpinBox):
    def __init__(self, minimum, maximum, step, decimals):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setSingleStep(step)
        self.setDecimals(decimals)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
