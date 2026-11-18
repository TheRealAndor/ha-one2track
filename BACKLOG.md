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

**🏅 Quality scale (Silver)**

- [ ] Register actions in async_setup
- [ ] Removal instructions in the README
- [ ] Test suite with more than 95% coverage
- [ ] PARALLEL_UPDATES on every platform
- [ ] Document the setup fields
- [ ] Check unavailable handling and logging
- [ ] Self-assessment and README note

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

## 🏅 Quality scale (Silver)

The rules of the [integration quality scale](https://contributors.home-assistant.io/core/quality-scale/rules/) that are still open for Bronze and Silver, based on a quick review of the code after v1.0.29.

### Register actions in async_setup

Bronze rule `action-setup`: actions are now registered from `async_setup_entry` (`async_setup_services` in `__init__.py`) and removed on unload. Register them once in `async_setup`, so they exist even when the config entry is not loaded, and raise `ServiceValidationError` when the targeted watch's entry is not loaded.

### Removal instructions in the README

Bronze rule `docs-removal-instructions`: add a short section on how to remove the integration (*Settings → Devices & services → One2Track → Delete*, then remove it in HACS or the Marketplace), and what stays behind.

### Test suite with more than 95% coverage

Silver rule `test-coverage` (and Bronze `config-flow-test-coverage`): add a pytest suite with `pytest-homeassistant-custom-component`.

- Config flow: success, invalid auth, cannot connect, unknown error, already configured, reauth (success, wrong account, invalid password)
- Coordinator, API parsing, entities, actions and events, with anonymised portal fixtures
- Includes *Automated tests for the message parser and event detection* above
- Run it in the Validate workflow and fail below 95% coverage

### PARALLEL_UPDATES on every platform

Silver rule `parallel-updates`: set `PARALLEL_UPDATES` in every platform module. `0` for read-only platforms that use the coordinator (sensor, binary_sensor, device_tracker, event), and `1` for platforms that send commands to the portal (button, select, switch), so commands do not hit the portal at the same time.

### Document the setup fields

Silver rule `docs-installation-parameters`: describe each field of the setup and re-authentication dialog in the README (username: the e-mail address of the One2Track portal account; password), with `data_description` texts in `translations/en.json`.

### Check unavailable handling and logging

Silver rules `entity-unavailable` and `log-when-unavailable`: verify that all entities become unavailable when the portal cannot be reached (also the entities that don't use the coordinator data directly), and that a lost connection is logged once and its recovery once, without extra warnings from the integration itself.

### Self-assessment and README note

The Marketplace has no official quality tiers; they are only awarded to core integrations. Once the Silver rules are met, add a `quality_scale.yaml` with the status of every rule (done, todo or exempt with a reason) and a short note in the README that the integration follows the Silver rules. Gold candidates already on this list: *Diagnostics download*, *Dutch translation*; other Gold rules to consider later are `icons.json`, a reconfigure flow, entity categories, repairs and known limitations.

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
