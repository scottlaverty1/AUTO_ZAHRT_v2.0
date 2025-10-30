# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# Do not replicate or redistribute without permission
# All rights reserved.
# ------------------------------------------------------------------------------

# core/methods/parser.py
import csv
from typing import Iterator
from .types import Command

def read_method_csv(path: str) -> Iterator[Command]:
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            yield Command(
                component=row.get('Component', '').strip(),
                action=row.get('Action', '').strip(),
                params=row.get('Parameters', '').strip(),
                notes=row.get('Notes', '').strip(),
                delay=float(row.get('delay') or 0.5),
            )

