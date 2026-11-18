# One2Track — Home Assistant Integration

[![Release](https://img.shields.io/github/v/release/TheRealAndor/ha-one2track)](https://github.com/TheRealAndor/ha-one2track/releases)
[![Validate](https://github.com/TheRealAndor/ha-one2track/actions/workflows/validate.yml/badge.svg)](https://github.com/TheRealAndor/ha-one2track/actions/workflows/validate.yml)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20me-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/therealandor) [![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white)](https://paypal.me/andorklink)

Custom Home Assistant integration for [One2Track](https://www.one2trackgps.com) GPS watches (children's and elderly trackers).

## Features

- **Device tracker** with GPS coordinates, zone detection, and address
- **15 sensors** — battery, SIM balance, signal strength, satellite count, speed, altitude, heading, GPS accuracy, steps today, steps total, status, timestamps, phonebook contact count, and whitelist number count (last two are model-dependent)
- **Phonebook & whitelist sensors** — show contact/number count with full list as attributes (only created if the device supports these features)
- **Binary sensor** — fall detection
- **Message event** — fires for each new message from the watch in the portal's Messages tab (event types `low_battery`, `sos`, `message`)
- **Buttons** — refresh location (activate GPS mode), find device (ring the watch)
- **Switch** — step counter toggle
- **Selects** — GPS tracking interval, profile/sound mode
- **19 services** — send message, force update, find device, intercom, set SOS number, set/add/remove phonebook contacts, set/add/remove whitelist numbers, set alarms, set quiet times, set language/timezone, change password, factory reset, remote shutdown, and a raw diagnostics service
- **Multi-model support** — automatically discovers each watch's capabilities (Connect MOVE, Connect UP, Connect NEXT, and others)
- **Device targeting** — all services support `entity_id`, `device_id`, and `area_id` targeting
- **Persistent settings** — phonebook, whitelist, alarms, and quiet times survive HA restarts

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to **Integrations** and click the three-dot menu in the top right
3. Select **Custom repositories**
4. Add `https://github.com/TheRealAndor/ha-one2track` with category **Integration**
5. Search for "One2Track" and install it
6. Restart Home Assistant
7. Go to **Settings > Devices & Services > Add Integration** and search for **One2Track**
8. Enter your One2Track portal username and password

### Manual

1. Copy the `custom_components/one2track` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via **Settings > Devices & Services**

## Supported Devices

The integration auto-discovers your watches and their capabilities. Tested with:

- **Connect UP** (model_id 77) — GPS interval code 0077, step counter code 0082
- **Connect MOVE** (model_id 27) — GPS interval code 0078, step counter code 0079, plus whitelist, intercom, and password change
- **Connect NEXT** (model_id 201 or 277) — GPS interval code 0077 (5 min / 10 min / 1 hour), step counter code 0082; no whitelist, intercom or password change

Other One2Track watch models should work — the integration discovers available commands dynamically rather than hardcoding per model.

## Using the integration

### What you get per watch

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

### On your dashboard

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

### Actions

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
| `get_raw_device_data` | Returns all raw data for troubleshooting, see [Diagnostics](#diagnostics) |

A few examples:

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

### Message events

Each watch gets an event entity (`event.<name>_message`) that fires when a new message from the watch appears in the portal's Messages tab, such as "Sam heeft op de SOS knop gedrukt!". The event data holds `message`, `sender`, `sent_at` (minute precision, in Home Assistant's time zone) and `urgent` (true when the portal shows the message in red, as it does for SOS). Messages you send to the watch are not fired. On first setup, existing messages are marked as seen and do not fire.

The event type is `sos` when the text contains "SOS", `low_battery` when it mentions a low battery, and `message` otherwise. The Dutch SOS and low-battery texts have been confirmed; for other alerts or languages, please open an issue with the exact text.

The portal is checked once per update (every 60 seconds), so an SOS reaches Home Assistant up to about a minute after it appears in the portal.

The entity's state is the time of the last event, and the UI shows the last event type (for example "SOS") until the next one. Every new message changes the time, so a state trigger fires for each message, also for a second SOS in a row. Exclude `unavailable` as in the [examples](#examples), or the automation also fires when the entity restores its state after a Home Assistant restart. Do not exclude `unknown`: that is the state before the very first event.

### Sending messages to the watch

The `one2track.send_message` action shows a text message on the watch's screen, just like the Messages tab in the portal. Messages can be at most 30 characters; longer ones are refused with an error.

```yaml
action: one2track.send_message
target:
  entity_id: device_tracker.sam
data:
  message: "Dinner is ready!"
```

### When your password changes

When the stored One2Track password stops working, Home Assistant shows a **Re-authenticate** notification. Click it and enter the new password; the integration reloads and all entities, history and automations stay as they were.

## Examples

The examples use a watch named **Sam**, so its entities are `device_tracker.sam`, `event.sam_message`, `button.sam_refresh_location` and so on. Replace `sam` with your watch's name, and `notify.mobile_app_my_phone` with your own phone.

### SOS: critical push notification with location

Breaks through silent mode and Do Not Disturb, and links to the watch's position on a map.

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

### SOS: get a fresh location and tell Sam help is coming

Asks the watch for a new GPS fix, replies on the watch's screen, and sends the updated position once it arrives.

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

### SOS: alarm in the house

Flashes the lights red and announces the SOS on your speakers, for when nobody is looking at their phone.

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

### Low battery: reminder to charge

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

### Time to come home

Sends a message to the watch at 18:00 on weekdays, only when Sam is not home yet.

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

## How It Works

There is no official One2Track API. This integration communicates with `www.one2trackgps.com` (a Ruby on Rails web application) by:

1. Authenticating via the login form with session cookies and CSRF tokens
2. Polling device state by scraping inline JavaScript variables from device pages
3. Refreshing base data from the JSON device list endpoint
4. Sending commands via form POSTs that mimic the web portal's PATCH requests
5. Reading the Messages tab for alerts from the watch

## Diagnostics

Call the `one2track.get_raw_device_data` service to get raw data from all sources (JSON API, HTML scraping, coordinator state, discovered capabilities). This is invaluable for debugging data issues.

## Changelog

See the [releases page](https://github.com/TheRealAndor/ha-one2track/releases) for what changed in each version; HACS shows the same notes when an update is available. For versions before v1.0.18, see the [original repository](https://github.com/jurrienk/ha-one2track).

## Support

If this integration saves you time or makes your smart home a little smarter, consider buying me a coffee. It's completely optional, but very much appreciated! ☕

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/therealandor)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white)](https://paypal.me/andorklink)

## Credits

This is a maintained fork of [jurrienk/ha-one2track](https://github.com/jurrienk/ha-one2track), which is no longer actively maintained.
