# FurryTail Home API notes (from MITM)

Captured 2026-08-10 against iOS FurryTail Home (`wuwei/1.0.16`).

**Do not commit `captures/*.mitm` — contains live JWTs and AWS temporary credentials.**

## Cloud

| Item | Value |
| --- | --- |
| Base URL | `https://app.prod-iot.furrytail.net` |
| Auth | `Authorization: <JWT>` (raw JWT, no `Bearer` prefix) |
| Locale header | `lang: en_US` |
| Envelope | `{ "code": 0, "tip": "...", "info"|"list": ..., "requestId": "..." }` |
| Product | `PF001` / "Smart cat litter machine" |
| productKey | `0002f3c7d847ce72` |
| Merchant | `吾尾物联网平台` (`merchantId` `100000000000000000`) |
| Realtime | AWS IoT Core `us-east-1` via `/device/add/policy` |

## Endpoints seen

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/app/user/get` | Current user profile |
| POST | `/home/place/list` | Homes/places |
| POST | `/home/place/index` | Place detail + `allDeviceList` |
| POST | `/device/query/device/property` | Device datapoints by `mac` |
| POST | `/device/v1/event/log/between/time` | Event history (`eids`, `startTime`, `endTime`, `mac`) |
| POST | `/pet/pet/info/list` | Pets in a place |
| POST | `/device/add/policy` | AWS IoT Cognito creds + MQTT topic |
| POST | `/device/upgrade/list` | Firmware channels (WiFi + MCU) |
| POST | `/device/upgrade/get` | Upgrade status |
| POST | `/app/v3/application/product/list` | Catalog |
| POST | `/msg/message/cnt` | Unread counts |
| POST | `/msg/push/switch/list` | Push switches |
| POST | `/cloud-message/mobile/set` | Push token registration |

## Login (probed)

`POST /app/user/login`

```json
{
  "merchantId": "100000000000000000",
  "account": "<email>",
  "password": "<password>",
  "lang": "en_US"
}
```

Returns `code: 0` with a user JWT (field name confirmed at runtime by the client’s token extractor). Authorization header on later calls is the raw JWT (no `Bearer` prefix).

## Not captured yet

- Command writes (clean / flatten / empty / light / schedule / DND)
- MQTT publish/subscribe payloads on the AWS IoT topic
- Exact login success JSON field names (client accepts several)

## Device identity (from place index)

- Name: Automatic Cat Litter Box
- Model: `PF001`
- Keyed by `mac` for property/event calls
- `onlineStatus`: boolean
- Firmware: WiFi `3.3.7_0026`, MCU `1.3.24`

## Property map (numeric DPs)

From `/device/query/device/property` `info` plus event correlation:

| DP | Observed | Likely meaning |
| --- | --- | --- |
| `onlineStatus` | bool | Cloud online |
| `20` | int (e.g. 29–77) | Visit duration (seconds?) — appears on toilet events |
| `21` | int (~5600–6700) | Cat weight grams — matches pet profiles |
| `24` | 0/1 | Cleaning / cycle state |
| `25` | `"true"` | Toilet / visit event flag (`eventId` 25) |
| `26` | `"true"` | Event flag (`eventId` 26) — often with `24` |
| `27` | `"true"` | Event flag (`eventId` 27) |
| `28` | `"true"` | Event flag (`eventId` 28) |
| `8` | `30` | Possibly clean delay (minutes) |
| `6` | `0/1` | Possibly auto-clean enable |
| `1`–`5`, `9`, `10`, `14`, `16`, `18`, `19`, `23`, `29` | mostly `0` | Unknown flags/enums |
| `12` | `"00"` | Unknown |
| `15`, `17` | `16000800` | Possibly schedule bitfields / times |
| `22` | `42` | Unknown (level? humidity?) |
| `30` | `1` | Unknown |
| `33` | `8` | Unknown |

## Events (`eids=25,26,28,27`)

| eventId | Role (inferred) | Payload notes |
| --- | --- | --- |
| 25 | Cat visit / weigh | Often includes `groupId` = pet id, `20` duration, `21` weight g |
| 26 / 27 / 28 | Cycle / clean related | Usually paired with DP `24` |

## AWS IoT (from `/device/add/policy`)

- Endpoint: `*-ats.iot.us-east-1.amazonaws.com`
- Topic shape: `granwin/<identityId>/message`
- Temporary `accessKeyId` / `secretKey` / `sessionToken` + Cognito `identityPoolId`
- Useful later for push updates; REST is enough for a v1 poller

## HA v1 candidate entities

From data already available (read-only):

- Device online
- Last visit time / duration / weight
- Per-pet weight (from pet list + visit events)
- Cleaning state (DP 24 + events)
- Firmware versions
- Waste / litter unknowns once DPs are decoded via command capture
