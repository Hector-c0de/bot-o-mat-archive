# BOT-O-MAT

## Overview:
BOT-O-MAT is a Python desktop app for creating robots, assigning timed household tasks, and running those tasks in parallel. Users can manage multiple robots, monitor live progress, and see leaderboard rankings based on type-specific scoring rules. The app persists robot/task state so sessions can be resumed, and it includes keyboard-accessible controls plus inline status feedback.

### TL;DR
If you only need to run the app quickly:

```bash
python3 --version
python3 -c "import tkinter; print('tkinter ok')"
sudo apt update && sudo apt install -y fonts-roboto && fc-cache -f -v
git clone https://github.com/RedVentures22/bot-o-mat-Hector-c0de.git
cd bot-o-mat-Hector-c0de
python3 -m src.gui
```

## Key Features
- Multi-robot management (add, edit, remove, select)
- Timed task execution for selected or all robots
- Live progress tracking with per-robot bars and overall summary
- Leaderboard with type-aware scoring and top-3 highlighting
- Persistent state saving/loading via `botomat_state.json`
- Inline status updates with reduced modal interruption
- Keyboard navigation support

## Tech Stack
- Backend: Python 3
- Frontend: Tkinter / ttk
- Environment: Linux and macOS (Roboto optional on Linux for intended typography)

## Getting Started
This project is optimized for Linux and macOS environments.

### 1. Prerequisites
Ensure you have Python 3.10 or higher installed:

```bash
python3 --version
```

Tkinter is required (it is included by default on macOS Python builds, but may require installation on some Linux distros):

```bash
python3 -c "import tkinter; print('tkinter ok')"
```

If needed on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3-tk
```

### 2. Installation
Clone the repository and move into the project folder:

```bash
git clone https://github.com/RedVentures22/bot-o-mat-Hector-c0de.git
cd bot-o-mat-Hector-c0de
```

No third-party Python packages are required for the GUI (`pip install` is not needed).

### 3. Optional: Match Intended UI Font
The app runs without this step, but to match the intended UI typography on Linux, install Roboto:

```bash
sudo apt update
sudo apt install fonts-roboto
fc-cache -f -v
```

Verify installation:

```bash
fc-list | grep -i "Roboto"
```

### 4. Running the Application
From the project root, start the GUI:

```bash
python3 -m src.gui
```

## Quick Usage
- Add one or more robots (name + type).
- Assign tasks to a selected robot or to all robots.
- Start, pause, resume, or cancel runs from Mission Command.
- Track progress and leaderboard updates live.

## Testing
Run the automated test suite from the project root:

```bash
python3 -m unittest discover -s tests -v
```

Alternative (pytest):

```bash
python3 -m pytest -q
```

## Test Coverage
Current automated coverage includes core logic and persistence/runtime helpers.

- Test files: `tests/test_scoring.py`, `tests/test_robot.py`, `tests/test_gui_state.py`, `tests/test_gui_run.py`
- Total tests: `15`
- Covered modules and areas:
	- `src/scoring.py`: task eligibility and score calculation
	- `src/robot.py`: task assignment and completion flow
	- `src/gui/state.py`: state serialization, parsing, save/load/delete
	- `src/gui/run.py`: runtime state setup, pause/resume, cancel restore, execution ticks

## Notes
- App state persists to `botomat_state.json`.
- No third-party Python dependencies are required.
- On some Linux systems, you may need the system package `python3-tk` for Tkinter GUI support.