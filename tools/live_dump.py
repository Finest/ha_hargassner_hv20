#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PKG_PATH = ROOT / "custom_components" / "hargassner_hv20"

# Load api.py without requiring Home Assistant to be installed locally.
pkg = types.ModuleType("hargassner_hv20")
pkg.__path__ = [str(PKG_PATH)]
sys.modules.setdefault("hargassner_hv20", pkg)
for name in ["channels", "api"]:
    spec = importlib.util.spec_from_file_location(f"hargassner_hv20.{name}", PKG_PATH / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"hargassner_hv20.{name}"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

from hargassner_hv20.api import HargassnerClient  # noqa: E402
from hargassner_hv20.channels import ANALOG_CHANNELS, DIGITAL_CHANNELS  # noqa: E402


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.178.59"
    frame = HargassnerClient(host).read_frame()
    print(f"tokens={len(frame.raw.split())} analog={len(frame.analog)} digital_words={len(frame.digital_words)}")
    print("\nAnalog:")
    for ch in ANALOG_CHANNELS:
        unit = ch.get("unit") or ""
        print(f"{ch['id']:03d} {ch['name']:<24} {str(frame.analog[ch['id']]):>8} {unit}")
    print("\nDigital words:", frame.digital_words)
    print("\nDigital channels:")
    for ch in DIGITAL_CHANNELS:
        print(f"D{ch['word']}.{ch['bit']:02d} {ch['name']:<24} {frame.digital[ch['key']]}")


if __name__ == "__main__":
    main()
