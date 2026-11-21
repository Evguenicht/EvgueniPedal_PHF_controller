MOZA INTEGRATION - PYTHON DEPENDENCIES
======================================

Recommended environment:
- Windows 10/11, 64-bit
- Python 3.11, 64-bit

Required third-party packages:
- PySide6: graphical user interface (moza_ui.pyw)
- pyserial: communication with the MOZA device over the COM port
- pyirsdk >= 1.3.7: iRacing telemetry SDK

The other telemetry readers in this version use Python standard-library
modules (ctypes, socket, struct, math, etc.) and require no extra package.
RaceRoom also requires no additional Python package.

INSTALLATION:
1. Install Python 3.11 64-bit and enable the Python Launcher (py).
2. Double-click install_requirements.bat.
3. Keep this folder alongside the application if you want to retain
   the dependency list and installer for future setups.

The application source requirements.txt is kept unchanged:
PySide6, pyserial, pyirsdk>=1.3.7.
