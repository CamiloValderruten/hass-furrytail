# FurryTail Integration Notes

This repository targets the newest FurryTail automatic litter box (`PF001`)
through the FurryTail Home / Granwin (吾尾) cloud. It is not a Tuya device.

## Cloud contract

- Base URL: `https://app.prod-iot.furrytail.net`
- Merchant ID: `100000000000000000`
- Locale header: `lang: en_US`
- Authentication header: `Authorization: <JWT>` with no `Bearer` prefix
- Login: `POST /app/user/login` with `merchantId`, `account`, `password`,
  `phoneCode: "1"`, and `lang`
- Successful login returns `token` and `refreshToken`
- Only one client session is valid per account. Home Assistant and the mobile
  app will invalidate each other's tokens. Use a separate real email account;
  `+` aliases are not accepted for this purpose.

Never commit captures, tokens, passwords, temporary AWS credentials, or
decompiled application artifacts.

## Device reads and writes

Devices are keyed by MAC address. Read properties with:

```text
POST /device/query/device/property
{"mac": "<MAC>", "lang": "en_US"}
```

The verified REST control path is:

```text
POST /device/control/device
{"mac": "<MAC>", "propertyMap": {"<DP>": <value>}}
```

Known writable datapoints:

| DP | Meaning | Value |
| --- | --- | --- |
| `3` | Clean | `1` triggers |
| `4` | Flatten | `1` triggers |
| `5` | Empty / change litter | `1` triggers; inferred, not physically tested |
| `22` | Night-light brightness | `0`–`100` |

Clean and flatten were physically verified. Their command DP changes to `1`
during the cycle and returns to `0`. DP `2` changes from `0` (idle) to `2`
(running). DP `24` stayed `1` both idle and running and must not be treated as
a confirmed cycle-state datapoint.

The mobile app's primary transport is MQTT at QoS 1:

```text
<productKey>/<MAC>/user/get
```

```json
{
  "data": {
    "22": {"type": 17, "value": 100}
  },
  "time": 1786400256
}
```

This is a Granwin topic, not an AWS Device Shadow update. REST is currently
used by the integration because it is simpler and has been verified.

## Recovery workflow

When the API changes:

1. Reproduce with the official app and a dedicated test account.
2. Capture HTTPS calls with a local MITM proxy; keep captures outside Git.
3. If controls bypass HTTP, inspect the current Android APK and Hermes bundle
   for endpoint paths, datapoint IDs, MQTT topics, and typed payloads.
4. Verify a suspected write with the REST endpoint before adding an entity.
5. Observe both the physical machine and property transitions until it returns
   to idle.
6. Update `docs/api-notes.md` with verified behavior and clearly label
   inferred behavior.

## Development

- Keep changes small and use existing coordinator/API helpers.
- Add a failing unit test before changing behavior.
- Run `python -m unittest discover -s tests -v`.
- Compile Python sources and validate JSON files before pushing.
- Use Conventional Commit subjects; Release Please derives versions and
  changelogs from them.
