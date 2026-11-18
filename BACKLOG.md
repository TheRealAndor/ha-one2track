# Backlog

Ideas and open work for upcoming versions. Tick an item when it ships and mention it in the release notes.

## Overview

**✨ Features**

- [ ] Diagnostics download
- [ ] Notify entity per watch
- [ ] Connectivity binary sensor (online/offline)
- [ ] Warning for low SIM balance
- [ ] Options flow: update interval and thresholds
- [ ] 12/24-hour time format select
- [ ] Safety zones from the portal
- [ ] Quiet times and alarms as entities
- [ ] Blueprint: smart GPS interval
- [ ] Dutch translation

**🧪 Quality**

- [ ] Automated tests for the message parser and event detection
- [ ] Verify re-authentication and session renewal in a real installation
- [ ] Collect alert texts for other languages and alert types
- [ ] Identical messages in the same minute are reported once

**🧹 Housekeeping**

- [ ] Submit to the HACS default repositories
- [x] Clean up the beta/1.0.27 branch

## ✨ Features

### Diagnostics download

Add Home Assistant's diagnostics platform, so users can click **Download diagnostics** on the integration or device page and attach the file to an issue.

- Include model ID, discovered capabilities, the merged device data and the coordinator state
- Redact personal data: phone numbers, phonebook, whitelist, coordinates, address, serial number, SIM details
- Can largely replace the `get_raw_device_data` action for bug reports (keep the action for now)

Why: the first "Unknown device" issue needed the model ID; with diagnostics a user can share it in one click.

### Notify entity per watch

Add a `notify` entity per watch, so `notify.send_message` works and the watch can be picked as a target for regular Home Assistant notifications.

- Reuse the existing `send_message` API call
- Enforce the portal's 30-character limit with a clear error, like the `send_message` action does
- Keep the `one2track.send_message` action for backwards compatibility

### Connectivity binary sensor (online/offline)

Add a binary sensor with device class `connectivity` that is on while the watch checks in regularly.

- Based on `last_communication`: off when the watch has not checked in for a set time (default to be decided, for example 30 minutes)
- Makes automations like "watch offline for 2 hours" simple; today this needs a template on `sensor.<name>_status` or the timestamp sensors
- The portal shows "online" in the map popup; check whether that flag is available in the scraped data before deriving it

### Warning for low SIM balance

When the prepaid balance runs out, the watch stops sending locations. Warn before that happens.

- Binary sensor (device class `problem`) that turns on below a threshold, and/or a repair issue in **Settings → Repairs**
- Threshold configurable through the options flow (see *Options flow* above), default for example EUR 2
- Only for watches that report a balance (`simcard.balance_cents`)

### Options flow: update interval and thresholds

Add an options flow (**Configure** button on the integration).

- Update interval, now fixed at 60 seconds (`DEFAULT_UPDATE_INTERVAL_SECONDS`); keep a sensible minimum so the portal is not hammered
- Threshold for the low SIM balance warning
- Possibly the offline timeout for the connectivity sensor

Note: the message events depend on the update interval; a longer interval delays SOS alerts. Mention this in the option's description.

### 12/24-hour time format select

The portal's Functions menu has **12/24hr weergave**. This is the only function from that menu without an entity or action.

- Find the command code and option values (capability discovery already lists the function; check its radio options)
- Add a select entity when the watch supports it, like the GPS interval and profile mode selects

### Safety zones from the portal

The portal has a **Veiligheidsgebieden** (safety zones) tab. Make these available in Home Assistant.

- First step: probe how the portal serves the zones (endpoint and format)
- Options: expose them as attributes on the tracker, or offer to create matching Home Assistant zones
- Home Assistant zones already work for presence, so this is mainly useful for people who manage zones in the One2Track app

### Quiet times and alarms as entities

Quiet times and alarms can only be changed through actions now. Make them usable from the dashboard.

- For example a switch per quiet-time window, or a "school mode" switch that applies a stored set of windows
- Possibly `time` entities for start and end, or a calendar entity that shows the windows and alarms
- The current values are already synced from the portal at startup and stored, so the state is known

### Blueprint: smart GPS interval

Provide an automation blueprint that saves battery: a fast GPS interval when the watch leaves a zone, and the slowest interval when it is home.

- Uses the existing `select.<name>_gps_tracking_interval`; the option labels differ per model and account language, so the blueprint should let the user pick the options
- Ship it in the repo (for example `blueprints/automation/one2track/smart_gps_interval.yaml`) with an import button in the README

### Dutch translation

Most One2Track users are Dutch, but all entity and config flow texts are English only (`translations/en.json`).

- Add `translations/nl.json` with the entity names, config flow, re-authentication and event type names
- Optionally also translate the action names and descriptions (`services` section in `strings.json`)

## 🧪 Quality

### Automated tests for the message parser and event detection

The message parsing and new-message detection were tested by hand against real portal output. Add pytest tests so this stays correct.

- `_parse_messages`: fixtures for incoming messages, a message sent from the portal (`rtl`, with "Verstuurd" after the time) followed by an SOS (this combination once swallowed the SOS), and the red `m--font-danger` SOS block
- `_async_fetch_new_messages`: first run marks existing messages as seen, a new message, two messages in the same minute, a restart, a watch without messages, portal messages are skipped
- Fixtures must be anonymised (no real names, avatars or UUIDs)
- Run the tests in the existing Validate workflow

### Verify re-authentication and session renewal in a real installation

Re-authentication (v1.0.27) was checked by code review only.

- Change the One2Track password, reload the integration: a **Re-authenticate** notification appears, the old password is refused, the new one works and entities stay
- Credentials of a different One2Track account are refused with `wrong_account`
- Over a day or more with debug logging: an expired session logs `Session expired, logging in again` and does **not** trigger re-authentication

### Collect alert texts for other languages and alert types

Message events classify alerts by their text. Confirmed so far (Dutch portal):

- SOS: `<name> heeft op de SOS knop gedrukt!` → `sos`
- Low battery: `<name> heeft een lage batterij!` → `low_battery`

Unknown:

- The texts in an English or German account (the English low-battery pattern `low batter` is an assumption)
- Whether other alerts appear in the Messages tab, such as a fall, leaving a safety zone or the watch being taken off, and their texts

Users who see an event of type `message` that should be something else can open an issue with the exact `message` attribute. Each confirmed text can become its own event type.

### Identical messages in the same minute are reported once

Portal messages have no ID and only minute precision, so they are recognised by date, time, sender, direction and text. Two identical messages from the same watch within the same minute (for example pressing SOS twice) fire only one event.

- Document this limitation in the Message events section of the README
- If the portal page turns out to contain an ID or exact timestamp anywhere, use that instead

## 🧹 Housekeeping

### Submit to the HACS default repositories

The repository passes all HACS checks (v1.0.26 and later). Remaining steps:

- Optionally let the original author (jurrienk/ha-one2track) know about the submission
- Fork `hacs/default`, add `TheRealAndor/ha-one2track` alphabetically to the `integration` file on a new branch
- Open the PR from a personal account and fill in the template completely
- After merge: update the README installation section (no custom repository needed anymore) and the HACS badge

Review can take months.

### Clean up the beta/1.0.27 branch

Done after v1.0.28: the README link in the v1.0.27b1 release notes now points to `main`, and `beta/1.0.27` and `beta/1.0.28` are deleted.

- Still open (optional): document the beta workflow (beta branch + pre-release) for future releases
