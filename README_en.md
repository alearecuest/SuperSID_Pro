# SuperSID Pro

SuperSID Pro is a real-time VLF (Very Low Frequency) signal monitoring and visualization system with a modern web interface.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Accessing the Web Interface](#accessing-the-web-interface)
- [Audio Input Configuration](#audio-input-configuration)
- [Simulation vs. Real Audio](#simulation-vs-real-audio)
- [Project Structure](#project-structure)
- [Development and Customization](#development-and-customization)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- Real-time VLF signal visualization from 27 international stations.
- Modern dashboard with individual station charts and an overview.
- Integrated space weather data display.
- Audio device selection from the web interface.
- Built-in simulation mode for hardware-free testing.
- WebSocket-based data streaming (FastAPI backend).

---

## Requirements

- Python 3.8 or newer.
- Linux recommended (for audio input and ALSA support).
- Modern web browser (Chrome, Edge, Firefox).
- Python dependencies listed in `requirements.txt`.

---

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/SuperSID_Pro.git
    cd SuperSID_Pro
    ```

2. (Optional) Set up a virtual environment:
    ```bash
    python3 -m venv SuperSID_Pro
    source SuperSID_Pro/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Running the Server

To launch the backend and web dashboard:

```bash
python3 web_server.py --port 8080 --debug
```
By default, the server will be available at:  
`http://localhost:8080`

---

## Accessing the Web Interface

- Open your web browser and go to:  
  `http://localhost:8080`
- On first launch, the setup page is shown.

---

## Audio Input Configuration

1. Go to "SETTINGS" or "Setup" in the web interface.
2. Choose your sound card, audio line-in, or microphone from the device list.
3. Save the configuration and restart monitoring (STOP/START).
4. When real audio is being used:
    - The terminal/console will display:
      `Starting real audio capture from device X`
    - The charts should show real, noisy, and unpredictable signals instead of perfectly smooth waves.

---

## Simulation vs Real Audio

- **Simulation:**  
  Generates artificial, perfectly smooth VLF signals for testing without hardware.

- **Real Audio:**  
  Signals are captured live from the selected audio device. Real VLF antennas produce noisy, dynamic signals that change if the input/disconnect is manipulated.

The system defaults to simulation if no audio device is configured or accessible.

---

## Project Structure

```
SuperSID_Pro/
│
├── src/
│   ├── web/
│   │   ├── api/                # FastAPI backend code
│   │   ├── static/             # Web assets (JS, CSS, images)
│   │   ├── templates/          # HTML templates (Jinja2)
│   │
│   ├── core/                   # Core logic: audio capture, VLF processing, weather, etc.
│   ├── data/                   # Temporary data and reporting
│
├── config/                     # Configuration files
├── requirements.txt            # Python dependencies
├── web_server.py               # Main entry point
└── README.md
```

---

## Development and Customization

- **Backend (API, simulation, audio capture):**
    - Code is located in `src/web/api/vlf_api.py` and `src/core/`.
    - To modify the simulation, add stations, or alter the use of real audio, edit this code.
    - The method `start_real_audio_capture(device_index, sample_rate, buffer_size)` is called to activate real audio capture (see below for integration).

- **Frontend (dashboard):**
    - Main JavaScript is in `src/web/static/js/dashboard.js`.
    - UI/graph customizations can be made here and in the CSS.

- **To add/update stations:**
    - Edit the configuration file, e.g. `config/default_config.json`.
    - Update frequencies, names, or monitoring options.

- **WebSocket streaming:**
    - Data is pushed in real time from backend to frontend via `/ws`.
    - Use browser DevTools (Network > WS) to inspect real-time messages.

- **Typical development workflow:**
    - Edit server or web files.
    - Stop and restart the backend server.
    - Hard-refresh the browser (Ctrl+Shift+R) to reload all assets.

---

## Troubleshooting

- **If you see perfectly regular signals:**  
  It is likely the system is in simulation mode. Check audio device selection in the web UI.

- **Terminal errors such as "cannot find card '0'" or "Unknown PCM":**  
  These indicate the system is not detecting your sound card with ALSA. Review your device connection and permissions.

- **Internal Server Error in browser:**  
  Likely a missing template or misconfiguration. Check terminal logs for Python tracebacks.

- **Noisy/blank charts:**  
  If using real audio, disconnecting/connecting the antenna/input should change the signals.

- **Listing available audio devices:**  
  Use the settings page. For backend troubleshooting, check the logs printed during startup or device selection.

- **Frontend debugging:**  
  Use browser DevTools (F12) to view console or network errors.

---

## License

This project is open source. See the `LICENSE` file for details.