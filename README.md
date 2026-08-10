# FurryTail for Home Assistant

Custom Home Assistant integration for **FurryTail Home** automatic litter boxes (Granwin / 吾尾 cloud — not Tuya).

Reverse-engineered from the FurryTail Home iOS app against `app.prod-iot.furrytail.net`.

## Features (v0.1 — read-only)

- Cloud online / cleaning state
- Last visit time, duration, weight, and pet
- Per-pet weight from the FurryTail pet profiles
- Clean delay + Wi‑Fi / MCU firmware versions

Commands (start clean, light, schedules) are not wired yet — needs a second MITM capture.

## Install (HACS)

1. HACS → Integrations → Custom repositories
2. Add `https://github.com/CamiloValderruten/hass-furrytail` as **Integration**
3. Install **FurryTail**, restart Home Assistant
4. Settings → Devices & services → Add Integration → **FurryTail**
5. Sign in with your FurryTail Home email + password

## Manual install

Copy `custom_components/furrytail` into your HA `custom_components` directory and restart.

## Notes

- Account auth uses `POST /app/user/login` with FurryTail’s merchant id.
- Device state is polled about every 2 minutes.
- Your password is stored in the HA config entry (same pattern as other cloud integrations). Prefer a dedicated app password if FurryTail ever adds one.

## Development

API notes from MITM: [`docs/api-notes.md`](docs/api-notes.md).
