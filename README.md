# Hargassner HV20 for Home Assistant

Custom Home Assistant integration for a **Hargassner HV20** wood boiler using the local TCP/Telnet DAQ stream.

> ⚠️ Current status: early project / tested on exactly one real device.  
> This integration is currently built and verified for **one specific HV20 installation** and should not be treated as a universal Hargassner integration yet.

## Tested device

This integration is currently known to work with:

- Manufacturer: **Hargassner**
- Boiler/model: **HV20**
- Build year: **2016**
- Firmware/software: **V10.2j**
- Hardware version: **V2.0h**
- Local protocol: TCP/Telnet stream on port **23**
- Example host/IP in the test installation: `192.168.178.59`

Other Hargassner models, newer/older firmware versions, pellet boilers, or different DAQ layouts may expose different channels or bit mappings. They are not supported unless their DAQ mapping is checked and adapted.

## What it does

The boiler exposes a local TCP stream on port 23. Each live frame starts with `pm` and then contains numeric values.

For the tested HV20, the frame layout is:

```text
pm + 162 analog values + 8 digital words
```

The integration maps those values into Home Assistant entities:

- `sensor` entities for analog values, for example:
  - Kesseltemperatur Ist
  - Rauchgastemperatur Ist
  - Sauerstoff O2 Ist
  - Puffer oben / Mitte / unten
  - Außentemperatur
  - Rücklauftemperatur Ist
  - Puffer Ladezustand
  - Kesselleistung
  - Störungsnummer
- `binary_sensor` entities for digital bitfields, for example:
  - Heizkreis-Pumpen
  - Mischer öffnet/schließt
  - Boiler-Anforderungen
  - Störung
  - Fremdwärme Freigabe/Pumpe

The channel mapping was generated from the boiler SD-card file:

```text
DAQ00000.DAQ
```

The DAQ metadata is decoded as `latin1`; the actual live stream is parsed as ASCII-like numeric tokens.

## What it does not do

- It does **not** control the boiler.
- It does **not** write to the boiler.
- It does **not** change parameters.
- It does **not** decode historic compressed DAQ log data.
- It is not yet a generic integration for all Hargassner devices.

It is currently read-only local polling.

## Installation

The Home Assistant integration domain/folder is:

```text
hargassner_hv20
```

The custom component must end up here:

```text
/config/custom_components/hargassner_hv20
```

After installation, Home Assistant needs a restart before the integration appears in the UI.

### Option A: HACS custom repository

Use this once the project has been published to GitHub.

1. Open Home Assistant.
2. Go to **HACS → Integrations**.
3. Open the three-dot menu.
4. Choose **Custom repositories**.
5. Add the repository URL, for example:

   ```text
   https://github.com/<owner>/ha_hargassner_hv20
   ```

6. Select category **Integration**.
7. Install **Hargassner HV20** from HACS.
8. Restart Home Assistant.
9. Go to **Settings → Devices & services → Add integration**.
10. Search for **Hargassner HV20**.
11. Enter the boiler host/IP and port.

Recommended initial values:

```text
Host: 192.168.178.59
Port: 23
Scan interval: 30 seconds
```

### Option B: Manual file copy

Copy this folder from the repository:

```text
custom_components/hargassner_hv20
```

to Home Assistant:

```text
/config/custom_components/hargassner_hv20
```

Then restart Home Assistant and add the integration via the UI.

### Option C: FTP upload

If your Home Assistant config directory is reachable via FTP:

1. Create the folder:

   ```text
   /config/custom_components/hargassner_hv20
   ```

2. Upload all files from:

   ```text
   custom_components/hargassner_hv20/
   ```

   into:

   ```text
   /config/custom_components/hargassner_hv20/
   ```

3. Restart Home Assistant.
4. Add the integration via the UI.

Example final layout:

```text
/config/custom_components/hargassner_hv20/
├── __init__.py
├── api.py
├── binary_sensor.py
├── channels.py
├── config_flow.py
├── const.py
├── coordinator.py
├── friendly_names.py
├── manifest.json
├── sensor.py
└── translations/
    ├── de.json
    └── en.json
```

## Configuration

After restart:

1. Open **Settings → Devices & services**.
2. Click **Add integration**.
3. Search for **Hargassner HV20**.
4. Enter:

   - Host/IP of the boiler
   - TCP port, usually `23`
   - Scan interval in seconds

The integration validates the connection by reading one live `pm` frame.

## Entity behavior

The tested boiler exposes many channels. Not every channel is useful for every installation.

Therefore:

- Core HV20 values are enabled by default.
- Many expansion/pellet/unused channels are created but disabled by default.
- You can enable additional entities manually in Home Assistant if needed.

This is intentional to avoid flooding Home Assistant with noisy or irrelevant entities.

## Notes about old template sensors

Before this integration, the test system used a raw TCP sensor and template sensors such as:

- `sensor.hargassner_hz1`
- `sensor.ofentemperatur`
- `sensor.abgastemperatur`
- `sensor.lambda`
- `sensor.puffertemperatur_oben`
- `sensor.puffertemperatur_mitte`
- `sensor.puffertemperatur_unten`
- `sensor.aussentemperatur`
- `sensor.pufferladung`
- `sensor.hz1leistung`

Those can be replaced by the new integration entities, for example:

| Old entity | New entity |
| --- | --- |
| `sensor.ofentemperatur` | `sensor.hargassner_hv20_kesseltemperatur_ist` |
| `sensor.abgastemperatur` | `sensor.hargassner_hv20_rauchgastemperatur_ist` |
| `sensor.lambda` | `sensor.hargassner_hv20_sauerstoff_o2_ist` |
| `sensor.hz1leistung` | `sensor.hargassner_hv20_kesselleistung` |
| `sensor.puffertemperatur_oben` | `sensor.hargassner_hv20_puffer_oben` |
| `sensor.puffertemperatur_mitte` | `sensor.hargassner_hv20_puffer_mitte` |
| `sensor.puffertemperatur_unten` | `sensor.hargassner_hv20_puffer_unten` |
| `sensor.pufferladung` | `sensor.hargassner_hv20_puffer_ladezustand` |
| `sensor.aussentemperatur` | `sensor.hargassner_hv20_aussentemperatur` |

If you also have separate Shelly temperature sensors for wood boiler flow/return, keep those separate and do not replace them blindly.

## Troubleshooting

### Integration does not appear

- Check that the folder is exactly:

  ```text
  /config/custom_components/hargassner_hv20
  ```

- Check that `manifest.json` is inside that folder.
- Restart Home Assistant.

### Cannot connect

- Check the boiler IP address.
- Check that TCP port `23` is reachable from Home Assistant.
- Check that the boiler sends a `pm ...` frame on connect.

### Entities are unavailable

- Confirm that the integration config entry was created successfully.
- Confirm the boiler stream still returns the expected number of values.
- For the tested HV20, a valid frame has `171` tokens:

  ```text
  pm + 162 analog values + 8 digital words
  ```

### Names or values look wrong

The mapping is DAQ-file dependent. If another firmware/model uses a different DAQ layout, `channels.py` must be regenerated from that device's `DAQ00000.DAQ`.

## Development

Useful local project files:

```text
custom_components/hargassner_hv20/channels.py  # generated channel mapping used by HA
tools/generate_channels.py                     # regenerates channels.py from a local DAQ dump
tools/live_dump.py                             # reads one live frame and prints mapped values
fixtures/sd_dump/                              # optional local-only dump folder, ignored by git
```

Raw SD-card dump/vendor files are intentionally not committed to the public repository. If you want to regenerate `channels.py`, place your own `DAQ00000.daq` in `fixtures/sd_dump/` locally first.

Run a basic syntax check:

```bash
python3 -m compileall custom_components/hargassner_hv20 tools
```

Read one live frame during development:

```bash
python3 tools/live_dump.py 192.168.178.59
```

Expected tested output summary:

```text
tokens=171 analog=162 digital_words=8
```

## Safety

This integration is intended to be read-only. It opens a TCP connection, reads a frame, parses it, and exposes values to Home Assistant. It should not send commands or write parameters to the boiler.

## License

TBD.
