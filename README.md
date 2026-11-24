<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/TheRealAndor/ha-one2track/main/custom_components/one2track/brand/dark_logo.png">
    <img src="https://raw.githubusercontent.com/TheRealAndor/ha-one2track/main/custom_components/one2track/brand/logo.png" alt="One2Track" width="400">
  </picture>
</p>

<h3 align="center">Keep an eye on the ones who matter, right from Home Assistant</h3>

<p align="center">
  Live location, battery, SOS alerts and two-way messages for One2Track GPS watches for kids and seniors.
</p>

<p align="center">
  <a href="https://github.com/TheRealAndor/ha-one2track/releases"><img src="https://img.shields.io/github/v/release/TheRealAndor/ha-one2track" alt="Release"></a>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS"></a>
  <a href="https://github.com/TheRealAndor/ha-one2track/actions/workflows/validate.yml"><img src="https://github.com/TheRealAndor/ha-one2track/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://ko-fi.com/therealandor"><img src="https://img.shields.io/badge/Ko--fi-Support%20me-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://paypal.me/andorklink"><img src="https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

## ✨ Highlights

- 📍 **Live location** on your map, with zones and street address
- 🆘 **SOS and low-battery alerts** as events, ready for your automations
- 💬 **Send messages** from Home Assistant straight to the watch's screen
- 🔔 **Find the watch** by making it ring, or get a fresh GPS fix with one tap
- ⚙️ **Manage the watch**: phonebook, quiet times, alarms, GPS interval, sound profile and more
- 🧠 **Works across models**: each watch's features are discovered automatically
- 🔑 **Password changed?** Home Assistant simply asks for the new one
- 🇳🇱 **In English and Dutch**, following your Home Assistant language
- 🩺 **Diagnostics** you can safely attach to an issue: personal data is removed

## 📑 Contents

- [Installation](#installation)
- [Migrating from jurrienk/ha-one2track](#migrating-from-jurrienkha-one2track)
- [Supported watches](#supported-watches)
- [Using the integration](#using-the-integration): [entities](#what-you-get-per-watch), [dashboard](#on-your-dashboard), [actions](#actions), [message events](#message-events), [sending messages](#sending-messages-to-the-watch)
- [Examples](#examples)
- [Troubleshooting](#diagnostics)
- [Removing the integration](#removing-the-integration)

<a id="installation"></a>
## 🚀 Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TheRealAndor&repository=ha-one2track&category=integration)

Or by hand:

1. Open HACS, click the three-dot menu in the top right and choose **Custom repositories**
2. Add `https://github.com/TheRealAndor/ha-one2track` with category **Integration**
3. Search for **One2Track**, install it and restart Home Assistant

> [!TIP]
> **Coming from jurrienk/ha-one2track?** Follow [Migrating from jurrienk/ha-one2track](#migrating-from-jurrienkha-one2track) below, so your configuration and entities stay.

Then add the integration:

[![Open your Home Assistant instance and start setting up One2Track.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=one2track)

Or go to **Settings → Devices & services → Add integration**, search for **One2Track** and log in with your One2Track portal username and password. All watches on your account appear automatically.

| Field | What to enter |
| - | - |
| **Username** | The username you use to log in to the [One2Track portal](https://www.one2trackgps.com) or the One2Track app |
| **Password** | The password of that account. If you change it later, Home Assistant asks for the new one ([details](#when-your-password-changes)) |

One account is enough for all watches linked to it; adding the same account twice is refused.

### Manual

1. Copy the `custom_components/one2track` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via **Settings → Devices & services**

<a id="migrating-from-jurrienkha-one2track"></a>
## 🔄 Migrating from jurrienk/ha-one2track

Both integrations use the same `one2track` folder and domain, so your configuration, entities, history and automations stay. Only the source of the integration has to change. The steps depend on where you installed jurrienk/ha-one2track from: the **Marketplace** built into recent Home Assistant versions, or **HACS**.

Make a backup first under *Settings → System → Backups*.

### Home Assistant Marketplace

> [!WARNING]
> **Never choose "Remove and uninstall"** on the jurrienk entry. That also deletes your One2Track configuration, including all entities and their history.

1. **Add this repository** (`https://github.com/TheRealAndor/ha-one2track`) as a custom repository (type **Integration**) and install **One2Track**. If that works, restart Home Assistant and you are done.
2. If the install is refused with *"The one2track directory belongs to jurrienk/ha-one2track"*, the jurrienk entry still claims the folder. Release it as follows.

<details>
<summary><b>Release the folder from the jurrienk entry</b></summary>

**a. Stop Home Assistant Core** from the console of the Home Assistant machine or an SSH connection from your computer (with the SSH add-on, its port must be enabled):

```
ha core stop
```

> [!IMPORTANT]
> Don't use the web terminal inside Home Assistant (*Terminal & SSH* in the sidebar): it runs through Home Assistant Core and stops working as soon as Core is stopped, so you could not start it again from there.

Home Assistant must be stopped, otherwise it overwrites the change below.

**b. Mark the jurrienk entry as not installed.** The file is `.storage/marketplace.repositories` in your configuration folder (`/config` or `/homeassistant`, depending on the add-on). Make a copy first, then change only the entry with `"full_name": "jurrienk/ha-one2track"`:

```diff
   "full_name": "jurrienk/ha-one2track",
   ...
-  "installed_commit": "02859d8",
-  "installed": true,
+  "installed": false,
   ...
-  "version_installed": "v1.0.17",
```

Or in one go with `jq`:

```bash
cd /config/.storage
cp marketplace.repositories marketplace.repositories.bak
jq '(.data[] | select(.full_name == "jurrienk/ha-one2track"))
    |= (.installed = false | del(.version_installed, .installed_commit))' \
  marketplace.repositories.bak > marketplace.repositories
```

**c. Start Home Assistant Core** again, from the console or SSH:

```
ha core start
```

**d. Install One2Track** from this repository. The red message is gone now. Restart Home Assistant once more afterwards.

If something goes wrong, stop Core again, put `marketplace.repositories.bak` back and start Core.

</details>

After the switch, updates come from this repository. The jurrienk entry usually disappears from the list by itself. If it is still there and removing it again offers to delete your configuration, cancel and leave it.

### HACS

In HACS, removing a repository deletes the files in `custom_components/one2track`, but not your configuration. The order matters: remove jurrienk first, then install this repository. The other way around, HACS deletes the files of this repository again.

1. In HACS, open **One2Track** (jurrienk/ha-one2track) and choose **Remove**. Don't restart Home Assistant yet.
2. Add `https://github.com/TheRealAndor/ha-one2track` as a custom repository (type **Integration**) and download **One2Track**.
3. Restart Home Assistant. Your One2Track configuration loads again with the new version.

If you restarted between step 1 and 2 by accident, the integration shows as *not loaded*. Your configuration is still there; it loads again after step 2 and 3.

> **Note:** "Steps today" starts counting from the moment you install the new version; from the next day on it matches the One2Track app. If you used the tracker's `battery_level` attribute or the address as the tracker state in automations, switch to the battery sensor or the `address` attribute.

<a id="supported-watches"></a>
## ⌚ Supported watches

| Model | Model ID | Notes |
|---|---|---|
| **Connect MOVE** | 27 | All features, including whitelist, intercom and PIN change |
| **Connect UP** | 77 | GPS interval and step counter |
| **Connect NEXT** | 189, 201, 277 | GPS interval (5 min, 10 min, 1 hour) and step counter; no whitelist, intercom or PIN change |
| **Connect YOU** | 377 | Reported by a user; functions are detected per watch |

Other One2Track watches should work too: the integration asks each watch which functions it supports instead of relying on a fixed list per model. The model name on the device page comes from the One2Track portal itself, so new models are named correctly as well. Still see `Unknown (…)`? Please [open an issue](https://github.com/TheRealAndor/ha-one2track/issues).

<a id="using-the-integration"></a>
## 🧭 Using the integration

<a id="what-you-get-per-watch"></a>
### 📦 What you get per watch

Each watch becomes a device in Home Assistant, named after the watch in the One2Track app. The entity IDs below are for a watch named **Sam**.

| Entity | What it does |
|---|---|
| `device_tracker.sam` | Location on the map, with `home`, the zone name or `not_home` as state. Attributes include `address`, `location_type` (GPS or WiFi) and the SIM balance |
| `sensor.sam_battery`, `sensor.sam_signal_strength`, `sensor.sam_sim_balance` | Battery level, mobile signal and prepaid balance |
| `sensor.sam_steps_today`, `sensor.sam_steps_total` | Steps counted today and in total (the step counter must be on) |
| `sensor.sam_status`, `sensor.sam_last_communication`, `sensor.sam_last_location_update` | How the watch is connected (`gps`, `wifi` or `offline`), when it last checked in and when it last sent a position |
| Speed, altitude, heading, GPS accuracy and satellite count | Details of the last GPS fix |
| `sensor.sam_phonebook`, `sensor.sam_whitelist` | Number of contacts and allowed numbers, with the full list as attributes (only on models that support them) |
| `binary_sensor.sam_fall_detected` | On when the watch detects a fall |
| `event.sam_message` | Fires for each new message from the watch, such as SOS and low battery. See [Message events](#message-events) |
| `button.sam_refresh_location` | Asks the watch for a fresh GPS position right now |
| `button.sam_find_device` | Makes the watch ring, to find it in the house |
| `button.sam_turn_off_watch` | Turns the watch off. It cannot be turned on again remotely |
| `switch.sam_step_counter` | Turns the step counter on or off |
| `select.sam_gps_tracking_interval` | How often the watch sends its position. More often means a fresher location and a shorter battery life |
| `select.sam_profile_mode` | Sound profile of the watch: sound and vibrate, sound only, vibrate only or silent |

The options of the selects come from the watch itself, so they differ per model and use the language of your One2Track account.

<a id="on-your-dashboard"></a>
### 🖥️ On your dashboard

A map and the most useful controls in one view:

```yaml
type: vertical-stack
cards:
  - type: map
    entities:
      - device_tracker.sam
    hours_to_show: 6
  - type: entities
    entities:
      - sensor.sam_battery
      - sensor.sam_last_location_update
      - event.sam_message
      - select.sam_gps_tracking_interval
      - button.sam_refresh_location
      - button.sam_find_device
```

<a id="actions"></a>
### 🎮 Actions

All actions start with `one2track.` and take the watch as target: an `entity_id` of any of its entities, a `device_id` or an `area_id`. Try them out in **Developer tools → Actions**.

| Action | What it does |
|---|---|
| `send_message` | Shows a text of at most 30 characters on the watch's screen |
| `force_update` | Fast GPS mode for about 2 minutes, for a fresh position |
| `find_device` | Makes the watch ring |
| `intercom` | Makes the watch call a phone number immediately |
| `set_sos_number` | Sets the number the watch calls when SOS is pressed |
| `set_phonebook`, `add_phonebook_contact`, `remove_phonebook_contact` | Manages the contacts on the watch |
| `set_whitelist`, `add_whitelist_number`, `remove_whitelist_number` | Manages the numbers allowed to call the watch (up to 10, Connect MOVE only) |
| `set_alarms` | Sets alarms on the watch |
| `set_quiet_times` | Sets up to 3 time windows in which the watch is silent |
| `set_language_timezone` | Sets the watch's language and UTC offset |
| `change_password` | Changes the 6-digit PIN of the watch |
| `factory_reset` | ⚠️ Resets the watch to factory settings. Cannot be undone |
| `remote_shutdown` | ⚠️ Turns the watch off. It cannot be turned on again remotely |
| `send_device_command` | Sends a raw command code, for advanced use |
| `get_raw_device_data` | Returns all raw data for troubleshooting, see [Troubleshooting](#diagnostics) |

A few examples:

<details>
<summary>Show examples</summary>

```yaml
# Contacts on the watch (replaces the whole list)
action: one2track.set_phonebook
target:
  entity_id: device_tracker.sam
data:
  contacts:
    - name: Mum
      number: "0031612345678"
    - name: Dad
      number: "0031687654321"
```

```yaml
# Silent at night and during the lunch break at school
action: one2track.set_quiet_times
target:
  entity_id: device_tracker.sam
data:
  windows:
    - start: "22:00"
      end: "07:00"
    - start: "12:00"
      end: "13:00"
```

```yaml
# Wake-up alarm at 07:00 on weekdays (format HH:MM-STATUS-MODE[-DAYS], days Mon to Sun)
action: one2track.set_alarms
target:
  entity_id: device_tracker.sam
data:
  alarms:
    - "07:00-1-3-1111100"
```

```yaml
# Let the watch call you now
action: one2track.intercom
target:
  entity_id: device_tracker.sam
data:
  phone_number: "0031612345678"
```

</details>

<a id="message-events"></a>
### 🆘 Message events

Each watch gets an event entity (`event.<name>_message`) that fires when a new message from the watch appears in the portal's Messages tab, such as "Sam heeft op de SOS knop gedrukt!". The event data holds `message`, `sender`, `sent_at` (minute precision, in Home Assistant's time zone) and `urgent` (true when the portal shows the message in red, as it does for SOS). Messages you send to the watch are not fired. On first setup, existing messages are marked as seen and do not fire.

The event type is `sos` when the text contains "SOS", `low_battery` when it mentions a low battery, and `message` otherwise. The Dutch SOS and low-battery texts have been confirmed; for other alerts or languages, please open an issue with the exact text.

The portal is checked once per update (every 60 seconds), so an SOS reaches Home Assistant up to about a minute after it appears in the portal.

The entity's state is the time of the last event, and the UI shows the last event type (for example "SOS") until the next one. Every new message changes the time, so a state trigger fires for each message, also for a second SOS in a row. Exclude `unavailable` as in the [examples](#examples), or the automation also fires when the entity restores its state after a Home Assistant restart. Do not exclude `unknown`: that is the state before the very first event.

<a id="sending-messages-to-the-watch"></a>
### 💬 Sending messages to the watch

The `one2track.send_message` action shows a text message on the watch's screen, just like the Messages tab in the portal. Messages can be at most 30 characters; longer ones are refused with an error.

```yaml
action: one2track.send_message
target:
  entity_id: device_tracker.sam
data:
  message: "Dinner is ready!"
```

<a id="when-your-password-changes"></a>
### 🔑 When your password changes

When the stored One2Track password stops working, Home Assistant shows a **Re-authenticate** notification. Click it and enter the new password; the integration reloads and all entities, history and automations stay as they were.

<a id="examples"></a>
## 💡 Examples

The examples use a watch named **Sam**, so its entities are `device_tracker.sam`, `event.sam_message`, `button.sam_refresh_location` and so on. Replace `sam` with your watch's name, and `notify.mobile_app_my_phone` with your own phone. Click **Show YAML** to copy an automation.

### 🆘 SOS: critical push notification with location

Breaks through silent mode and Do Not Disturb, and links to the watch's position on a map.

<details>
<summary>Show YAML</summary>

```yaml
automation:
  - alias: "Sam pressed SOS"
    triggers:
      - trigger: state
        entity_id: event.sam_message
        not_from: unavailable
        not_to: unavailable
    conditions:
      - condition: state
        entity_id: event.sam_message
        attribute: event_type
        state: sos
    actions:
      - action: notify.mobile_app_my_phone
        data:
          title: "🆘 SOS from Sam"
          message: "{{ trigger.to_state.attributes.message }}"
          data:
            url: >-
              https://maps.google.com/?q={{ state_attr('device_tracker.sam', 'latitude') }},{{ state_attr('device_tracker.sam', 'longitude') }}
            # iOS: critical alert
            push:
              sound:
                name: default
                critical: 1
                volume: 1.0
            # Android: alarm channel, delivered immediately
            ttl: 0
            priority: high
            channel: alarm_stream
```

</details>

### 📍 SOS: get a fresh location and tell Sam help is coming

Asks the watch for a new GPS fix, replies on the watch's screen, and sends the updated position once it arrives.

<details>
<summary>Show YAML</summary>

```yaml
automation:
  - alias: "Sam SOS: locate and reply"
    triggers:
      - trigger: state
        entity_id: event.sam_message
        not_from: unavailable
        not_to: unavailable
    conditions:
      - condition: state
        entity_id: event.sam_message
        attribute: event_type
        state: sos
    actions:
      - action: button.press
        target:
          entity_id: button.sam_refresh_location
      - action: one2track.send_message
        target:
          entity_id: device_tracker.sam
        data:
          message: "Help is on the way!"
      - wait_for_trigger:
          - trigger: state
            entity_id: sensor.sam_last_location_update
        timeout: "00:05:00"
      - action: notify.mobile_app_my_phone
        data:
          title: "📍 Sam's location"
          message: "{{ state_attr('device_tracker.sam', 'address') or 'Updated position' }}"
          data:
            url: >-
              https://maps.google.com/?q={{ state_attr('device_tracker.sam', 'latitude') }},{{ state_attr('device_tracker.sam', 'longitude') }}
```

</details>

### 🚨 SOS: alarm in the house

Flashes the lights red and announces the SOS on your speakers, for when nobody is looking at their phone.

<details>
<summary>Show YAML</summary>

```yaml
automation:
  - alias: "Sam SOS: alarm in the house"
    triggers:
      - trigger: state
        entity_id: event.sam_message
        not_from: unavailable
        not_to: unavailable
    conditions:
      - condition: state
        entity_id: event.sam_message
        attribute: event_type
        state: sos
    actions:
      - action: light.turn_on
        target:
          area_id: living_room
        data:
          color_name: red
          brightness_pct: 100
          flash: long
      - action: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          media_player_entity_id: media_player.living_room
          message: "Attention! Sam pressed the SOS button."
```

</details>

### 🔋 Low battery: reminder to charge

A nudge on your phone when the watch runs low.

<details>
<summary>Show YAML</summary>

```yaml
automation:
  - alias: "Sam's watch needs charging"
    triggers:
      - trigger: state
        entity_id: event.sam_message
        not_from: unavailable
        not_to: unavailable
    conditions:
      - condition: state
        entity_id: event.sam_message
        attribute: event_type
        state: low_battery
    actions:
      - action: notify.mobile_app_my_phone
        data:
          message: "🔋 Sam's watch is almost empty, time to charge it."
```

</details>

### 🏠 Time to come home

Sends a message to the watch at 18:00 on weekdays, only when Sam is not home yet.

<details>
<summary>Show YAML</summary>

```yaml
automation:
  - alias: "Sam, time to come home"
    triggers:
      - trigger: time
        at: "18:00:00"
    conditions:
      - condition: time
        weekday: [mon, tue, wed, thu, fri]
      - condition: not
        conditions:
          - condition: state
            entity_id: device_tracker.sam
            state: home
    actions:
      - action: one2track.send_message
        target:
          entity_id: device_tracker.sam
        data:
          message: "Time to come home!"
```

</details>

<a id="removing-the-integration"></a>
## 🗑️ Removing the integration

1. Go to **Settings → Devices & services → One2Track**, click the three-dot menu next to the account and choose **Delete**. This removes the watches, their entities and the stored settings from Home Assistant; nothing changes on the watches or in the One2Track portal.
2. To also remove the files, remove **One2Track** in HACS (or the Marketplace), or delete `custom_components/one2track` if you installed it manually, and restart Home Assistant.
3. Automations and dashboard cards that use the One2Track entities are not removed automatically; edit or delete them yourself.

<a id="diagnostics"></a>
## 🩺 Troubleshooting

**Download diagnostics** when you open an issue: go to **Settings → Devices & services → One2Track**, click the three-dot menu and choose **Download diagnostics** (or do the same on the page of one watch). The file contains the model, the watch's state and the functions it supports. Names, phone numbers, contacts, location, serial numbers and login details are removed, so you can attach it safely.

For deeper digging, the `one2track.get_raw_device_data` action returns the raw data from all sources (JSON API, HTML scraping, coordinator state, discovered capabilities). Unlike diagnostics, this output is **not** anonymised.

To see what the integration is doing, open **Settings → Devices & services → One2Track**, click the three-dot menu and choose **Enable debug logging**. Disable it again to download the log, and attach it to your issue.

## 🔧 How it works

There is no official One2Track API. This integration communicates with `www.one2trackgps.com` (a Ruby on Rails web application) by:

1. Authenticating via the login form with session cookies and CSRF tokens
2. Polling device state by scraping inline JavaScript variables from device pages
3. Refreshing base data from the JSON device list endpoint
4. Sending commands via form POSTs that mimic the web portal's PATCH requests
5. Reading the Messages tab for alerts from the watch

## 📜 Changelog

See the [releases page](https://github.com/TheRealAndor/ha-one2track/releases) for what changed in each version; HACS shows the same notes when an update is available. For versions before v1.0.18, see the [original repository](https://github.com/jurrienk/ha-one2track).

## ☕ Support

If this integration saves you time or makes your smart home a little smarter, consider buying me a coffee. It's completely optional, but very much appreciated! ☕

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/therealandor)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white)](https://paypal.me/andorklink)

## 🙏 Credits

This is a maintained fork of [jurrienk/ha-one2track](https://github.com/jurrienk/ha-one2track), which is no longer actively maintained.
