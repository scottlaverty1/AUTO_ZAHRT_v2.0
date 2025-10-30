# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# Do not replicate or redistribute without permission
# All rights reserved.
# ------------------------------------------------------------------------------

# core/methods/types.py
from dataclasses import dataclass

@dataclass
class Command:
    component: str
    action: str
    params: str
    notes: str = ""
    delay: float = 0.25

def parse_kv_params(s: str) -> dict:
    """Turn 'a=1, b=2' into {'a': '1', 'b': '2'} (string values by design)."""
    out = {}
    if not s:
        return out
    for part in s.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            out[k.strip()] = v.strip()
    return out
