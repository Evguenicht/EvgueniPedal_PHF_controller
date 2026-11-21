MOZA ACTIVE PEDAL — TELEMETRY INTEGRATION (v1.5 — AUTOMOBILISTA 2)

CONTENTS
- moza_ui.pyw: configuration interface (English UI).
- moza_controller.py: main controller for all integrated games.
- moza_protocol.py: captured MOZA communication frames.
- forza_horizon_6.py: Forza Horizon 6 UDP telemetry reader.
- raceroom_telemetry.py: RaceRoom shared-memory reader (API 3.6+).
- ams2_telemetry.py: Automobilista 2 shared-memory reader (Project CARS 2 format, v14).
- test_ams2_telemetry.py: synthetic tests for the AMS2 decoder.
- moza_settings.json: configuration file created/updated by the UI.
- requirements.txt: external Python dependencies.

INSTALLATION
1. Keep all application files in the same folder.
2. Install Python 3.11 64-bit (recommended).
3. Install dependencies: py -3.11 -m pip install -r requirements.txt
4. Launch the UI: py -3.11 moza_ui.pyw
5. Select the game, configure the COM port and alerts, then click Save Settings.
6. Launch the controller: py -3.11 moza_controller.py

DEPENDENCIES
- PySide6: graphical interface.
- pyserial: MOZA serial communication.
- pyirsdk >= 1.3.7: iRacing SDK access.
AMS2 requires no additional Python package.

IMPORTANT
- moza_settings.json is read at controller startup. Restart the controller
  after changing settings.
- Alert frequencies: 10, 20, 30, 40, 50, 60, 70, 80, 90 and 100 Hz.
- Each alert has its own frequency and intensity.
- The predictive warning adjusts its effective speed using the maximum wheel
  slip, bounded between 0 and 1: effective_speed = speed * max(0, 1 - k * max_slip).
  The coefficient k is configurable from 0 to 3.
- Profiles are independent for LMU, AC, ACR, FH6, iRacing, F1 26, AC EVO,
  RaceRoom and AMS2.
- If haptic feedback is disabled, telemetry can still be read but no vibration
  commands are sent.
- Do not run the UI hardware test and the controller simultaneously; both must
  not open the same MOZA COM port.
- Keep moza_protocol.py beside the application scripts. The MOZA frames are
  captured protocol frames, not mathematically generated waveforms.

FORZA HORIZON 6
1. Enable Data Out in the HUD and Gameplay settings.
2. Set Data Out IP to 127.0.0.1.
3. Set the UDP port to the same value as the FH6 profile (default 20444).
4. Save the FH6 profile and launch the controller.

LE MANS ULTIMATE
- The vehicle class is read from mVehicleClass in TelemInfoV01.
- HYP retains the existing mGripFract-based detector. LMP2 ELMS, LMP2, LMP3
  and GTE use per-wheel longitudinal slip estimated from wheel rotation and
  longitudinal ground velocity. GT3 lock detection/prediction remain disabled
  in this version; the predictive brake warning remains available.
- LMU class-specific predictive warning settings override global settings
  when a recognized class is detected.

VERSION 1.2 — iRACING AND F1 26
iRacing uses shared memory through pyirsdk and reads Speed, Brake, Throttle,
LFspeed, RFspeed, LRspeed and RRspeed. The SDK publishes at approximately 60 Hz.
F1 26 uses UDP telemetry format 2026, default port 20777, and combines Car
Telemetry (ID 6) and Motion Ex (ID 13) packets by frame identifier.

VERSION 1.3 — ASSETTO CORSA EVO
- Reads Local\acevo_pmf_physics.
- Uses packetId, gas, brake, speedKmh and per-wheel slipRatio.
- Wheel order: FL, FR, RL, RR.

VERSION 1.4 — RACEROOM RACING EXPERIENCE
- Reads the Windows shared-memory mapping $R3E (API 3.6+).
- Uses vehicle speed, pedals and per-wheel linear wheel speed.
- Wheel order: FL, FR, RL, RR.

VERSION 1.5 — AUTOMOBILISTA 2
- Adds an independent AMS2 profile.
- Reads the Windows shared-memory mapping $pcars2$ in read-only mode.
- In AMS2, open Options > System and set Shared Memory to Project CARS 2.
- The reader requires shared-memory version 14 and uses mSequenceNumber to
  avoid reading a page while the game is updating it.
- Read fields include mSpeed, mBrake, mThrottle, mAntiLockActive, mTyreRPS,
  mTyreFlags, mTyreSlipSpeed and mTyreGrip. The header marks mTyreSlipSpeed
  and mTyreGrip OBSOLETE; they are exposed for diagnostics only.
- Wheel order: FL, FR, RL, RR.
- No documented active per-wheel linear-speed field is used by this reader.
  The current estimate is a relative wheel-speed deficit: slip_i = 1 -
  abs(RPS_i) / max(abs(RPS of all four wheels)), clamped to 0..1. This is a
  relative comparison, not an absolute physical longitudinal slip ratio.
  Validate it on track, especially through corners, before calibrating thresholds.
- Polling is capped at 200 Hz. No extra Python dependency is required.

AMS2 SETUP
1. Start AMS2 and open Options > System.
2. Set Shared Memory to Project CARS 2 and apply the setting.
3. Enter a driving session.
4. Select Automobilista 2 in the MOZA interface.
5. Save settings and launch moza_controller.py.
6. The console should report that AMS2 shared memory is connected.

VALIDATION STATUS
- Python syntax compilation passed.
- Five synthetic decoder tests passed: decoding, wheel order, duplicate/odd
  sequence filtering and rejection of an unsupported memory version.
- No live AMS2 session or MOZA hardware test has been performed in this
  environment. The relative mTyreRPS slip estimate still requires on-track
  validation, first on a straight and then in corners.


UPDATE — MULTI-GAME TYRE-WEAR INPUT (PHF)

The “Tire wear coefficient” now affects games whose telemetry exposes a usable
per-wheel wear measurement:
- Le Mans Ultimate: mWear (fraction worn, 0 = new, 1 = worn), already supported.
- Automobilista 2: mTyreWear (fraction worn, 0 = new, 1 = worn).
- iRacing: average of inner/middle/outer tread remaining, converted from percent
  remaining to a fraction worn.
- F1 26: Car Damage packet (ID 10), m_tyresWear (percent worn).

The coefficient is shared across games in the global predictive warning;
LMU class-specific settings still take precedence for LMU. A value of 0 disables
wear influence. The factor is: 1 - coefficient * maximum_wheel_wear.

AVAILABILITY LIMITATIONS
- Forza Horizon 6: the FH6 Data Out format does not transmit TireWear.
- RaceRoom: the shared-memory API used here exposes whether tire wear is active,
  but not an individual wear measurement for the four tires.
- Assetto Corsa EVO: the shared-memory tyreWear field is reported as unpopulated
  in currently documented builds; it is not used.
- Assetto Corsa: tyreWear exists, but behaves as a non-linear grip/health signal
  affected by warm-up; it is not treated as monotonic degradation in this version.
- Assetto Corsa Rally: no sufficiently documented per-wheel wear measurement
  was identified for this integration.

When a game does not provide wheel_wear, the wear factor remains neutral; no
fabricated value is substituted. No live game or PHF hardware test was performed
in this environment.


INTEGRATION — ASSETTO CORSA COMPETIZIONE (ACC)

- Added an independent ACC profile to both configuration interfaces.
- Read-only Windows shared-memory access:
  Local\\acpmf_physics and Local\\acpmf_static.
- The dedicated acc_telemetry.py reader retrieves vehicle speed, brake input,
  wheel angular speeds and the four-wheel slipRatio array.
- Wheel order: FL, FR, RL, RR.
- ACC provides signed slipRatio: braking slip is negative and acceleration slip
  is positive. The reader sends max(0, min(1, -slipRatio)) to the common detector.
- ACC documents tyreRadius in the static page as unused; the reader does not
  attempt to reconstruct slip from that field.
- Minimum/maximum slip thresholds, prediction, vibration intensity and
  frequency use ACC's own game profile. Other game profiles are unchanged.
- ACC shares the acpmf_* mapping names with Assetto Corsa; the controller opens
  the pages for the selected game only.
- ACC tire-wear telemetry is not yet used by the predictive brake warning;
  only braking/slip telemetry is integrated.

ACC VALIDATION
- Synthetic slip tests cover matched wheel/vehicle speed, locked wheel,
  faster-than-ground wheel, wheel ordering and low-speed guard.
- Python syntax compilation passed.
- A live ACC session and the static tire-radius values still require
  validation on the user's PC.
