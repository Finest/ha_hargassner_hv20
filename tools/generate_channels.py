#!/usr/bin/env python3
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DAQ = ROOT / "fixtures" / "sd_dump" / "DAQ00000.daq"
OUT = ROOT / "custom_components" / "hargassner_hv20" / "channels.py"

def read_daq_xml(path: Path) -> str:
    data = path.read_bytes().decode("latin1", errors="replace")
    start = data.index("<DAQPRJ>")
    end = data.index("</DAQPRJ>") + len("</DAQPRJ>")
    return data[start:end]

def slug(s: str) -> str:
    s = s.replace("°", "deg")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return s or "channel"

def main():
    root = ET.fromstring(read_daq_xml(DAQ))
    analog = []
    for ch in root.find("ANALOG") or []:
        analog.append({
            "id": int(ch.attrib["id"]),
            "key": f"a{int(ch.attrib['id']):03d}_{slug(ch.attrib.get('name',''))}",
            "name": ch.attrib.get("name", f"Analog {ch.attrib['id']}"),
            "unit": ch.attrib.get("unit") or None,
            "dop": int(ch.attrib.get("dop", "1")),
        })
    digital = []
    for ch in root.find("DIGITAL") or []:
        digital.append({
            "word": int(ch.attrib["id"]),
            "bit": int(ch.attrib["bit"]),
            "key": f"d{int(ch.attrib['id']):02d}_{int(ch.attrib['bit']):02d}_{slug(ch.attrib.get('name',''))}",
            "name": ch.attrib.get("name", f"Digital {ch.attrib['id']}.{ch.attrib['bit']}"),
        })
    header = '# Generated from fixtures/sd_dump/DAQ00000.daq by tools/generate_channels.py\n'
    OUT.write_text(
        header
        + "ANALOG_CHANNELS = " + repr(analog) + "\n\n"
        + "DIGITAL_CHANNELS = " + repr(digital) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}: {len(analog)} analog, {len(digital)} digital")

if __name__ == "__main__":
    main()
