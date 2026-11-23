# EvgueniPedal PHF

**An experimental pedal haptic feedback application for sim racing.**

EvgueniPedal PHF is a Python-based application designed to enhance sim racing immersion and driving awareness through real-time haptic feedback on accelerator and brake pedals with the Moza PHF (for now).

By analyzing telemetry data provided by supported racing simulators, the application translates important vehicle behaviours into vibrations, helping drivers better understand what is happening at the tyre-road interface.

### Key Features

- **Brake Lock Detection:** Detects wheel lock-up during braking.
- **Predictive Brake Warnings:** Provides early haptic feedback when wheel lock is likely to occur.
- **Understeer & Oversteer Detection:** Experimental detection based on wheel slip and steering input.
- **Customizable Haptic Feedback:** Adjust vibration frequency and intensity.
- **Game-Specific Profiles:** Configure detection parameters independently for supported simulators.

### Project Status

EvgueniPedal PHF is actively under development.

Some features, particularly understeer and oversteer detection in Le Mans Ultimate and Automobilista 2, are experimental and still require testing and calibration.

See the [Releases](../../releases) section for stable versions and experimental pre-releases.
