# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# Do not replicate or redistribute without permission
# All rights reserved.
# ------------------------------------------------------------------------------

# core/methods/logger.py
import csv, time
from pathlib import Path
from datetime import datetime

class RunLogger:
    def __init__(self, out_dir: str, run_name: str):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')
        self.path = Path(out_dir) / f"{ts}_{run_name}.csv"
        self._fh = open(self.path, 'w', newline='', encoding='utf-8')
        self._w = csv.writer(self._fh)
        self._w.writerow(['Time_s','Component','Action','Parameters','Output','Notes'])
        self._t0 = time.time()

    def write(self, comp, act, params, out, notes=""):
        t = round(time.time() - self._t0, 2)
        self._w.writerow([t, comp, act, params, out, notes])
        self._fh.flush()
        print(f"[{t:7.2f}] {comp:12} | {act:18} | {out}")

    def close(self):
        self._fh.close()
