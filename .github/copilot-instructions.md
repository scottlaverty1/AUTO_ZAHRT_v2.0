# Copilot / AI assistant instructions — AutoZahrt

Short, actionable guidance to help an AI agent be productive in this repository.

1) Purpose / Big picture
- This repository is a Python-based automation framework for lab hardware (pumps, liquid handlers, temperature controllers, detectors, etc.).
- High-level intent: define device interfaces in `devices/` and provide concrete drivers in `devices/*_devices/`. The GUI builders live in `gui/`. Experiment "methods" live in `methods/` and small test harnesses live in `test/`.

2) Key files & directories (quick map)
- `main.py` — intended top-level runner (currently empty). Don't assume it contains orchestration yet.
- `devices/` — device interface stubs (e.g., `pumps.py`, `liquid_handlers.py`, `temperature_controllers.py`, `uv_detectors.py`, `valves.py`, `hplc.py`, `uplcms.py`). Implementations go in subfolders:
  - `devices/pump_devices/` (examples: `harvard_syringe_pumps.py`, `vici_m6_pumps.py`)
  - `devices/liquid_handler_devices/` (examples: `ender3_liquid_handlers.py`, `gx_liquid_handlers.py`)
  - `devices/temperature_controller_devices/` (example: `TC720.py`)
- `gui/` — GUI builder scripts (e.g., `config_builder.py`, `methods_builder.py`, `uv_detector_gui.py`). These are small tools for composing experiment configurations and methods.
- `methods/` — place where experiment method logic belongs (file: `methods/methods.py`).
- `test/` — small, ad-hoc tests or runners (currently `test/test.py`).

3) Coding and structural conventions discovered here
- Interface vs implementation split: devices/<thing>.py defines the intended API/abstraction; device-specific drivers are placed under `devices/<thing>_devices/<driver>.py`.
- File naming: snake_case module names. Driver module names include vendor or model (e.g., `harvard_syringe_pumps.py`, `ender3_liquid_handlers.py`).
- Minimal dependencies: repository currently contains stub files and placeholders. Many files are intentionally skeletal — when adding code, prefer small, isolated modules and add a simple example usage in `test/`.

4) How an AI agent should make changes
- When adding a new driver:
  - Create or update `devices/<category>.py` only if you need to add a new abstract API; otherwise place implementation under `devices/<category>_devices/<vendor_model>.py`.
  - Export a small, well-documented class (constructor, connect/disconnect, and the specific control methods). Keep side-effects minimal.
  - Add a short example or unit-style script in `test/` that imports the driver and exercises one method.
- When adding a new experiment method: put it in `methods/methods.py` (or add a new module in `methods/`), and add a small example invocation to `test/` demonstrating input shape.

5) Developer workflows and commands (what actually runs now)
- There is no established top-level build or test runner present. Practical dev runs today are:
  - Run small scripts directly: `python test/test.py` (or run `python path/to/script.py`).
  - If you add a test suite, use `pytest` (`python -m pytest`) — add a `requirements.txt` if you introduce external packages.
- Debugging: run the specific module in a debugger / interactive REPL. There is no CI configured in the repository yet.

6) Integration points & external dependencies to watch for
- Hardware integrations are intended (serial, USB, or vendor SDK). No vendor libraries are committed — add them to `requirements.txt` if needed and document install steps.
- Be conservative when adding blocking hardware calls; prefer an injectable connection object so tests can run without hardware.

7) Examples to cite for PRs
- To add a pump driver, create `devices/pump_devices/<vendor_model>.py` matching the naming in `devices/pumps.py` and include a short `if __name__ == "__main__":` example or a `test/` snippet.
- To add GUI wiring, follow the pattern in `gui/config_builder.py` and `gui/methods_builder.py` (these are currently skeletons — keep changes minimal and documented).

8) Safety and delivery notes for AI edits
- Avoid committing secrets or hardware credentials. If a change requires a credential, add a placeholder and document where to populate it (do not add real values).
- If adding new external packages, add a `requirements.txt` with pinned versions and update this file.

If anything in these notes is unclear or you'd like a stricter template (for example a driver template or a method template), tell me which template you want and I will add it to this file.
