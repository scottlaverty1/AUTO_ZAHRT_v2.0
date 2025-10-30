# core/methods/runner.py
import threading, time
from typing import Optional
from .types import Command, parse_kv_params
from .logger import RunLogger
from .resolve import (
    resolve_temperature, resolve_valve, resolve_pump, resolve_harvard, resolve_gx281
)
from auto_zahrt.devices import DeviceRegistry  # adjust your import

class MethodRunner:
    def __init__(self, registry: DeviceRegistry, logger: RunLogger, pause_event: Optional[object] = None):
        self.registry = registry
        self.logger = logger
        self.pause_event = pause_event
        self._pump_threads: list[threading.Thread] = []

    def run(self, commands: list[Command]) -> None:
        for cmd in commands:
            # pause-aware
            while self.pause_event and self.pause_event.is_set():
                self.log.write("SYNC", "paused", "", "Waiting for troubleshooting")
                time.sleep(1.0)
            self._execute(cmd)
            time.sleep(cmd.delay)
        self.wait_for_pumps()

    # ---------- core dispatch ----------
    def _execute(self, cmd: Command) -> None:
        c = cmd.component
        a = cmd.action
        p = cmd.params

        if c.upper() == "SYNC" and a == "wait_for_pumps":
            return self.wait_for_pumps()

        if c == "Temperature":
            return self._do_temperature(a, p)

        if c in ("VICI-6Way", "VICI-10Way", "VICI-24Way"):
            return self._do_valve(a, p)

        if c == "Pump":
            return self._do_pump(a, p)

        if c == "HarvardPump":
            return self._do_harvard(a, p)

        if c == "GX-281":
            return self._do_gx281(a, p)

        self.log.write(c, a, p, "Error: Invalid Component")

    # ---------- components ----------
    def _do_temperature(self, action: str, params: str):
        d = parse_kv_params(params)
        temp = float(d["temp"])
        temp_id = int(d.get("temp_id", "1"))
        name = resolve_temperature(self.registry, temp_id)
        dev = self.registry.get("temperature_controllers", name) if name else None
        if not dev:
            return self.log.write("Temperature", action, params, f"Error: controller {temp_id} not found")
        if action == "set_temperature":
            dev.set_temperature(temp)
            self.log.write("Temperature", action, params, f"set {temp}")
        elif action == "read_temperature":
            t = dev.read_temperature()
            self.log.write("Temperature", action, params, f"{t:.2f} °C")
        else:
            self.log.write("Temperature", action, params, "Error: unknown action")

    def _do_valve(self, action: str, params: str):
        d = parse_kv_params(params)
        valve_id = int(d.get("valve_id", "-1"))
        position = d.get("position")
        targets = []

        if valve_id == -1:
            for n in self.registry.list_names("valves"):
                dev = self.registry.get("valves", n)
                if dev: targets.append(dev)
        else:
            name = resolve_valve(self.registry, valve_id)
            dev = self.registry.get("valves", name) if name else None
            if dev: targets.append(dev)

        if not targets:
            return self.log.write("VICI", action, params, f"Error: valve {valve_id} not found")

        for v in targets:
            if action == "move_home" and hasattr(v, "move_home"):
                v.move_home(); self.log.write("VICI", action, params, f"Homed {valve_id}")
            elif action == "go_to_position" and position is not None and hasattr(v, "go_to_position"):
                p = int(position)
                v.go_to_position(p)
                if hasattr(v, "check_current_position"):
                    cur = v.check_current_position()
                    self.log.write("VICI", action, params, f"-> {p} (now {cur})")
                else:
                    self.log.write("VICI", action, params, f"-> {p}")
            else:
                self.log.write("VICI", action, params, "Error: bad action/params")

    def _do_pump(self, action: str, params: str):
        d = parse_kv_params(params)
        flow = float(d["flow_rate"]); vol = float(d["volume"]); pid = int(float(d["pump_id"]))
        name = resolve_pump(self.registry, pid)
        pump = self.registry.get("pumps", name) if name else None
        if not pump: return self.log.write("Pump", action, params, f"Error: Pump {pid} not found")
        if action not in ("aspirating", "dispensing"):
            return self.log.write("Pump", action, params, "Error: invalid action")
        if flow <= 0 or vol <= 0:
            return self.log.write("Pump", action, params, "Skipped: non-positive rate/volume")

        est = abs(vol) / (abs(flow) / 60.0)
        def job():
            try:
                if hasattr(pump, "start"): pump.start()
                if hasattr(pump, "set_flow_rate"): pump.set_flow_rate(abs(flow), action)
                if hasattr(pump, "pump_solution"): pump.pump_solution(vol)
                if hasattr(pump, "stop"): pump.stop()
                self.log.write("Pump", action, params, f"ok {abs(vol)} uL @ {flow} uL/min", notes=f"~{est:.1f}s")
            except Exception as e:
                self.log.write("Pump", action, params, f"Error: {e}")

        th = threading.Thread(target=job, daemon=True)
        th.start(); self._pump_threads.append(th)
        self.log.write("Pump", action, params, "started", notes=f"~{est:.1f}s")

    def _do_harvard(self, action: str, params: str):
        d = parse_kv_params(params)
        pid = int(float(d["pump_id"]))
        name = resolve_harvard(self.registry, pid)
        pump = self.registry.get("pumps", name) if name else None
        if not pump: return self.log.write("HarvardPump", action, params, f"Error: Pump {pid} not found")

        if action == "select_syringe" and hasattr(pump, "select_syringe"):
            syr = int(d["syringe"]); pump.select_syringe(syr)
            self.log.write("HarvardPump", action, params, f"syr={syr}")

        elif action == "infuse" and hasattr(pump, "infuse_volume"):
            vol = float(d["volume"]); rate = float(d["rate"])
            def job():
                try:
                    pump.infuse_volume(vol, rate)
                    self.log.write("HarvardPump", action, params, "done")
                except Exception as e:
                    self.log.write("HarvardPump", action, params, f"Error: {e}")
            th = threading.Thread(target=job, daemon=True)
            th.start(); self._pump_threads.append(th)
            self.log.write("HarvardPump", action, params, f"started {vol} uL @ {rate}")

        elif action == "stop" and hasattr(pump, "stop"):
            pump.stop(); self.log.write("HarvardPump", action, params, "stopped")
        else:
            self.log.write("HarvardPump", action, params, "Error: unknown/unsupported action")

    def _do_gx281(self, action: str, params: str):
        d = parse_kv_params(params)
        did = int(d.get("device_id", "1"))
        name = resolve_gx281(self.registry, did)
        inst = self.registry.get("liquid_handlers", name) if name else None
        if not inst: return self.log.write("GX-281", action, params, f"Error: {did} not found")
        if action == "move_home" and hasattr(inst, "home"):
            inst.home(); self.log.write("GX-281", action, params, "Homed")
        elif action == "move_xy" and hasattr(inst, "move_xy"):
            x, y = int(d["x"]), int(d["y"]); inst.move_xy(x, y)
            self.log.write("GX-281", action, params, f"XY=({x},{y})")
        elif action in ("move_z_height", "move_z") and hasattr(inst, "move_z"):
            z = int(d.get("height", d.get("z", "0"))); inst.move_z(z)
            self.log.write("GX-281", action, params, f"Z={z}")
        else:
            self.log.write("GX-281", action, params, "Error: unknown/unsupported action")

    # ---------- sync helpers ----------
    def wait_for_pumps(self):
        for th in self._pump_threads:
            th.join()
        self._pump_threads.clear()
        self.log.write("SYNC", "wait_for_pumps", "", "All pumps finished")
