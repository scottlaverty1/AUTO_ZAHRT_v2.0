# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# Do not replicate or redistribute without permission
# All rights reserved.
# ------------------------------------------------------------------------------

# core/methods/resolve.py
from typing import Optional
from auto_zahrt.devices import DeviceRegistry  # adjust import to your path

def first_or_none(names):
    for n in names:
        if n is not None:
            return n
    return None

def resolve_temperature(reg: DeviceRegistry, temp_id: int) -> Optional[str]:
    # try common naming conventions; tweak to your registry’s actual names
    candidates = [
        f"TC720_{temp_id}",
        f"Temperature_{temp_id}",
        f"temp_{temp_id}",
    ]
    for n in candidates:
        if reg.get("temperature_controllers", n):
            return n
    # fallback: single device in category
    names = reg.list_names("temperature_controllers")
    return names[0] if names else None

def resolve_valve(reg: DeviceRegistry, valve_id: int) -> Optional[str]:
    for n in (f"Valve_{valve_id}", f"ViciValve_{valve_id}", f"vici_{valve_id}"):
        if reg.get("valves", n):
            return n
    names = reg.list_names("valves")
    return names[0] if names else None

def resolve_pump(reg: DeviceRegistry, pump_id: int) -> Optional[str]:
    for n in (f"Pump_{pump_id}", f"VICI_M6_{pump_id}", f"vici_pump_{pump_id}"):
        if reg.get("pumps", n):
            return n
    names = reg.list_names("pumps")
    return names[0] if names else None

def resolve_harvard(reg: DeviceRegistry, pump_id: int) -> Optional[str]:
    for n in (f"HarvardPump_{pump_id}", f"PhdUltra_{pump_id}"):
        if reg.get("pumps", n):
            return n
    # some labs separate Harvard into same 'pumps' category; adjust if needed
    names = [n for n in reg.list_names("pumps") if "Harvard" in n or "PhdUltra" in n]
    return names[0] if names else None

def resolve_gx281(reg: DeviceRegistry, device_id: int = 1) -> Optional[str]:
    for n in (f"GX281_{device_id}", "GX281", "gx281"):
        if reg.get("liquid_handlers", n):
            return n
    names = reg.list_names("liquid_handlers")
    return names[0] if names else None
