#!/usr/bin/env python3
from __future__ import annotations

import importlib
from pathlib import Path

OPS = {
    "gmail": "gmail_ops",
    "google-calendar": "calendar_ops",
    "google-drive": "drive_ops",
    "google-docs": "docs_ops",
    "google-sheets": "sheets_ops",
    "google-slides": "slides_ops",
    "linear": "linear_ops",
    "ramp": "ramp_ops",
}


def run(script_path: Path) -> None:
    service = script_path.parent.name
    operation = script_path.stem.replace("-", "_")
    module_name = OPS.get(service)
    if module_name is None:
        raise SystemExit(f"Unknown script service directory: {service}")
    module = importlib.import_module(f"_lib.{module_name}")
    handler = getattr(module, operation, None)
    if handler is None:
        raise SystemExit(f"No Python handler for {service}/{script_path.name}")
    handler()
