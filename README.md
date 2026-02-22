# Green-grid 🌲🔋

**Green-grid** is a real-time data center power optimization simulator. It visualizes server load, predicts energy consumption using Machine Learning, and employs an autonomous "Green Agent" to optimize power usage by consolidating workloads.

---

## 🚀 Features

- **Real-Time Simulation**: Powered by `simpy`, simulating dynamic workloads and server states (Active/Sleep).
- **TUI Dashboard**: A sleek Terminal User Interface built with `textual` and `textual-plotext` for live monitoring.
- **ML Energy Forecast**: Uses a `RandomForestRegressor` to predict future power consumption and detect anomalies.
- **Green Agent Optimizer**: An autonomous agent that moves tasks to consolidate loads and put idle servers to sleep.
- **Stress Testing**: Built-in commands to simulate load spikes and system stress.

---

## 🛠️ Architecture

- `tui_app.py`: The main entry point and UI dashboard.
- `grid_engine.py`: Core simulation logic and server management.
- `ml_predictor.py`: Intelligence layer for power forecasting.
- `optimizer.py`: Heuristic-based agent for power efficiency.
- `config.py`: Global constants (server count, power ratings, simulation speed).

---

## 📦 Installation

Ensure you have Python 3.8+ installed. Install the required dependencies:

```bash
pip install simpy textual textual-plotext scikit-learn numpy
```

---

## 🎮 Usage

Launch the simulation dashboard:

```bash
python3 tui_app.py
```

### Keyboard Shortcuts
- `O`: Toggle the **Green Agent** (Optimizer) ON/OFF.
- `Ctrl+C`: Exit the application.

### Terminal Commands (In-App)
Type these into the app's command input to interact with the grid:
- `add [amount]`: Inject a one-time load spike (e.g., `add 50`).
- `remove [amount]`: Manually drain load from the grid (e.g., `remove 30`).
- `stress [amount] [duration]`: Start a sustained stress test (e.g., `stress 100 50`).
- `toggle`: Same as pressing `O`.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
