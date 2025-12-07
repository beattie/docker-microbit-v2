# microbit-ble-dev Learning Plan

**Project Goal**: Expand BLE and GATT knowledge through hands-on Rust development on micro:bit v2

**Base**: Forked from `ble-joystick` (381-line working BLE joystick implementation)

**Learning Approach**: Self-paced, hands-on implementation with detailed guidance and verification steps

---

## Phase 1: Add Button A/B Characteristics

**Learning Objectives**:
- Understand GATT characteristic properties (READ, NOTIFY)
- Work with Embassy GPIO async APIs
- Implement button debouncing in embedded Rust
- Extend existing GATT service with new characteristics

### Implementation Steps

#### 1.1 Define Button Characteristics in GATT Service

**Current Service** (src/main.rs:82-107):
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,
}
```

**Task**: Add two new characteristics for buttons
```rust
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    button_a: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,  // 0 = released, 1 = pressed
```

**Files to Modify**:
- `src/main.rs:82-107` - Add button fields to `JoystickService` struct

**References**:
- TrouBLE GATT macro documentation: Look at existing x_axis/y_axis examples
- Test files already reference these UUIDs: `test/test_buttons.py:24-25`

---

#### 1.2 Update Shared Data Structure

**Current Structure** (src/main.rs:109-114):
```rust
struct JoystickData {
    x: u16,
    y: u16,
}
```

**Task**: Add button state fields
```rust
struct JoystickData {
    x: u16,
    y: u16,
    button_a: u8,
    button_b: u8,
}
```

**Files to Modify**:
- `src/main.rs:109-114` - Extend `JoystickData` struct
- `src/main.rs:232` - Update initialization in `joystick_read_task()`

**Learning**: How async tasks share data via `Signal<ThreadModeRawMutex, T>`

---

#### 1.3 Create Button Reading Task

**Goal**: Create a new Embassy task that reads button states and updates the signal

**Task**: Implement `button_read_task()`
```rust
#[embassy_executor::task]
async fn button_read_task() {
    // Get button GPIO pins from board
    let btn_a = ...  // Get from board.btn_a
    let btn_b = ...  // Get from board.btn_b

    // Configure as inputs with pull-up resistors
    // micro:bit buttons are active-low (pressed = LOW)

    loop {
        // Read button states
        let a_pressed = !btn_a.is_high();  // Invert because active-low
        let b_pressed = !btn_b.is_high();

        // Get current joystick data
        let mut data = JOYSTICK_SIGNAL.wait().await;

        // Update button states
        data.button_a = if a_pressed { 1 } else { 0 };
        data.button_b = if b_pressed { 1 } else { 0 };

        // Signal updated data
        JOYSTICK_SIGNAL.signal(data);

        // Sample at 50Hz (20ms) for responsive button feel
        Timer::after_millis(20).await;
    }
}
```

**Files to Create/Modify**:
- `src/main.rs` - Add new task function (suggest after `joystick_read_task()`)
- `src/main.rs:365-366` - Spawn the new task in `main()`

**micro:bit Button Details**:
- Button A: Row 1, Column 5 (board.btn_a)
- Button B: Row 1, Column 2 (board.btn_b)
- Active-low: Pressed = GND (LOW), Released = VCC (HIGH via pull-up)
- Debouncing: 20ms sample rate provides natural debouncing

**Embassy GPIO References**:
- `embassy_nrf::gpio::Input` - GPIO input pin
- `embassy_nrf::gpio::Pull::Up` - Enable internal pull-up resistor
- `.is_high()` / `.is_low()` - Synchronous read methods

---

#### 1.4 Update Connection Task to Handle Buttons

**Current Handling** (src/main.rs:291-321):
```rust
async fn connection_task(...) {
    loop {
        select(
            gatt_server.next(),
            JOYSTICK_SIGNAL.wait(),
        ).await;

        // Only updates x_axis and y_axis
    }
}
```

**Task**: Add button notification logic
```rust
// After updating x_axis and y_axis
if let Err(e) = service.button_a_notify(&conn, &data.button_a) {
    defmt::warn!("Failed to notify button A: {}", e);
}

if let Err(e) = service.button_b_notify(&conn, &data.button_b) {
    defmt::warn!("Failed to notify button B: {}", e);
}
```

**Files to Modify**:
- `src/main.rs:291-321` - Update `connection_task()` notification logic

**Learning**: How GATT notifications push data to connected clients

---

#### 1.5 Testing Plan

**Quick Test**:
```bash
cd microbit-ble-dev
cargo build --release
cargo run --release
```

**Python Test** (already provided):
```bash
cd microbit-ble-dev/test
python test_buttons.py
```

**Expected Output**:
```
Connected to microbit-joy
Initial values:
  X-Axis: 512
  Y-Axis: 512
  Button A: Released
  Button B: Released

Press Button A...
  Button A: PRESSED

Release Button A...
  Button A: Released
```

**Web Bluetooth Test**: Open `test/ble-test.html` in Chrome/Edge

**Verification Checklist**:
- [ ] Code compiles without errors
- [ ] Device advertises as "microbit-joy"
- [ ] Can connect via nRF Connect or Python script
- [ ] GATT service shows 4 characteristics (X, Y, Button A, Button B)
- [ ] Button notifications arrive when pressing physical buttons
- [ ] No warnings in defmt logs

---

## Phase 2: Modularize Code Structure

**Learning Objectives**:
- Organize embedded Rust projects into logical modules
- Understand Rust module system and visibility
- Separate concerns (hardware, BLE, application logic)
- Prepare codebase for complex features

### Implementation Steps

#### 2.1 Create Module Directory Structure

**Target Structure**:
```
src/
├── main.rs          (100 lines) - Entry point, executor, spawning
├── gatt.rs          (80 lines)  - GATT service definitions
├── tasks/
│   ├── mod.rs       (10 lines)  - Module exports
│   ├── ble.rs       (150 lines) - BLE stack and app tasks
│   ├── joystick.rs  (80 lines)  - Joystick/button reading
│   └── led.rs       (30 lines)  - LED status indication
└── lib.rs           (20 lines)  - Shared types and constants
```

**Tasks**:
```bash
cd microbit-ble-dev/src
mkdir tasks
touch lib.rs gatt.rs tasks/mod.rs tasks/ble.rs tasks/joystick.rs tasks/led.rs
```

**Learning**: Cargo module resolution, `mod` declarations, `pub use`

---

#### 2.2 Extract GATT Service Definition

**Move**: `JoystickService` struct and `JoystickData` from main.rs to gatt.rs

**src/gatt.rs**:
```rust
use trouble_host::prelude::*;

/// GATT Service for Joystick with Buttons
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
pub struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    pub x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    pub y_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    pub button_a: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    pub button_b: u8,
}

/// Shared data structure for joystick state
#[derive(Clone, Copy)]
pub struct JoystickData {
    pub x: u16,
    pub y: u16,
    pub button_a: u8,
    pub button_b: u8,
}
```

**src/main.rs**: Add module declaration
```rust
mod gatt;
use gatt::{JoystickService, JoystickData};
```

**Files to Create**:
- `src/gatt.rs` - New file with service definitions

**Files to Modify**:
- `src/main.rs` - Remove service definitions, add `mod gatt;`

**Learning**: Public API design, re-exporting types

---

#### 2.3 Extract Task Modules

**Goal**: Move each async task to its own module

**src/tasks/led.rs**:
```rust
use embassy_executor::Spawner;
use embassy_time::Timer;
use microbit_bsp::Microbit;

#[embassy_executor::task]
pub async fn led_blink_task(mut led: /* type */) {
    // Move led_blink_task implementation here
}
```

**src/tasks/joystick.rs**:
```rust
use embassy_executor::Spawner;
use embassy_time::Timer;
use embassy_sync::signal::Signal;
use crate::gatt::JoystickData;

pub static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();

#[embassy_executor::task]
pub async fn joystick_read_task(/* params */) {
    // Move joystick_read_task implementation here
}

#[embassy_executor::task]
pub async fn button_read_task(/* params */) {
    // Move button_read_task implementation here
}
```

**src/tasks/ble.rs**:
```rust
use embassy_executor::Spawner;
use trouble_host::prelude::*;
use crate::gatt::{JoystickService, JoystickData};
use crate::tasks::joystick::JOYSTICK_SIGNAL;

#[embassy_executor::task]
pub async fn mpsl_task(/* params */) { /* ... */ }

#[embassy_executor::task]
pub async fn ble_runner_task(/* params */) { /* ... */ }

#[embassy_executor::task]
pub async fn ble_app_task(/* params */) { /* ... */ }

async fn connection_task(/* params */) { /* ... */ }

async fn advertise(/* params */) { /* ... */ }
```

**src/tasks/mod.rs**:
```rust
pub mod led;
pub mod joystick;
pub mod ble;

pub use led::led_blink_task;
pub use joystick::{joystick_read_task, button_read_task, JOYSTICK_SIGNAL};
pub use ble::{mpsl_task, ble_runner_task, ble_app_task};
```

**src/main.rs** (simplified):
```rust
mod gatt;
mod tasks;

use gatt::{JoystickService, JoystickData};
use tasks::*;

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    // Initialize hardware
    // Spawn tasks
}
```

**Files to Create**:
- `src/tasks/mod.rs`, `src/tasks/led.rs`, `src/tasks/joystick.rs`, `src/tasks/ble.rs`

**Files to Modify**:
- `src/main.rs` - Remove task definitions, add `mod tasks;`

**Learning**: Module privacy, `pub` visibility, static items in modules

---

#### 2.4 Create Shared Library Module

**Goal**: Centralize constants and shared types

**src/lib.rs**:
```rust
#![no_std]

/// BLE device name advertised to clients
pub const DEVICE_NAME: &str = "microbit-joy";

/// Joystick update interval (milliseconds)
pub const JOYSTICK_UPDATE_MS: u64 = 100;

/// Button polling interval (milliseconds)
pub const BUTTON_UPDATE_MS: u64 = 20;

// Re-export common types
pub use gatt::{JoystickService, JoystickData};

pub mod gatt;
```

**Usage in main.rs**:
```rust
use microbit_ble_dev::{DEVICE_NAME, JOYSTICK_UPDATE_MS};
```

**Files to Create**:
- `src/lib.rs` - Shared library definitions

**Learning**: Library crates vs binary crates, `#![no_std]`

---

#### 2.5 Testing Plan

**Verification**:
```bash
cargo build --release
# Should compile with same binary size (±5%)

cargo run --release
# Should function identically to before refactoring
```

**Checklist**:
- [ ] Code compiles without warnings
- [ ] All tasks spawn correctly
- [ ] BLE functionality unchanged (test with Python script)
- [ ] Binary size approximately the same
- [ ] No new defmt warnings

**Learning Checkpoint**: Compare git diff to understand what moved where

---

## Phase 3: Add Standard Battery Service

**Learning Objectives**:
- Implement a standard Bluetooth SIG GATT service
- Understand standard UUIDs and characteristic formats
- Read ADC for battery voltage monitoring
- Handle multiple GATT services in one device

### Implementation Steps

#### 3.1 Understand Battery Service Specification

**Standard Battery Service**:
- Service UUID: `0x180F` (16-bit standard)
- Battery Level Characteristic UUID: `0x2A19` (16-bit)
- Format: u8 (0-100%)
- Properties: READ, NOTIFY
- Descriptor: Client Characteristic Configuration (auto-added for NOTIFY)

**References**:
- Bluetooth SIG GATT Specifications: https://www.bluetooth.com/specifications/specs/battery-service/
- Already documented in `GATT.md:710-751`

**Learning**: Difference between custom UUIDs (128-bit) and standard UUIDs (16-bit)

---

#### 3.2 Define Battery Service in GATT

**src/gatt.rs**: Add new service
```rust
/// Standard Bluetooth Battery Service
#[gatt_service(uuid = "180F")]  // Note: 16-bit UUID for standard service
pub struct BatteryService {
    #[characteristic(uuid = "2A19", read, notify)]
    pub battery_level: u8,  // 0-100%
}
```

**Learning**:
- TrouBLE supports both 16-bit and 128-bit UUIDs
- Standard services improve compatibility with generic BLE apps

---

#### 3.3 Calculate Battery Level from VDD

**micro:bit v2 Power**:
- Powered by USB (5V) or battery pack (2x AAA = 3V)
- nRF52833 VDD range: 1.7V - 3.6V
- Internal voltage: Accessible via SAADC channel VDD with 1/6 prescaler

**Task**: Create battery reading function
```rust
// In src/tasks/joystick.rs or new src/tasks/battery.rs

use embassy_nrf::saadc::{Saadc, Config, ChannelConfig, VddInput};

async fn read_battery_voltage(saadc: &mut Saadc) -> u8 {
    // Configure SAADC for VDD measurement
    // VDD measurement gives internal voltage (1.7-3.6V range)

    // Read raw ADC value (12-bit = 0-4095)
    let raw = saadc.sample(&VddInput).await;

    // Convert to voltage (mV)
    // VDD/6 with 0.6V reference => voltage = raw * 6 * 600 / 4095
    let voltage_mv = (raw as u32 * 3600) / 4095;

    // Map to percentage (assume 3.0V = 100%, 2.2V = 0%)
    let percent = if voltage_mv >= 3000 {
        100
    } else if voltage_mv <= 2200 {
        0
    } else {
        ((voltage_mv - 2200) * 100 / 800) as u8
    };

    percent
}

#[embassy_executor::task]
pub async fn battery_read_task(/* saadc, signal */) {
    loop {
        let level = read_battery_voltage(&mut saadc).await;
        BATTERY_SIGNAL.signal(level);

        // Update every 60 seconds (battery changes slowly)
        Timer::after_secs(60).await;
    }
}
```

**Challenge**: SAADC is already used by joystick_read_task
- **Option A**: Share SAADC via mutex
- **Option B**: Combine battery reading into joystick_read_task
- **Option C**: Use sequential channel sampling

**Files to Modify**:
- `src/tasks/joystick.rs` or create `src/tasks/battery.rs`

**Learning**:
- ADC internal channels
- Voltage-to-percentage mapping
- Resource sharing in Embassy

---

#### 3.4 Add Battery Service to GATT Server

**Current** (src/tasks/ble.rs):
```rust
let server = gatt_server.build(&gatt_resources)
    .add_service(JoystickService::new())
    .build();
```

**Update**: Add battery service
```rust
let server = gatt_server.build(&gatt_resources)
    .add_service(JoystickService::new())
    .add_service(BatteryService::new())
    .build();
```

**Files to Modify**:
- `src/tasks/ble.rs` - Update server builder
- `src/gatt.rs` - Add `BatteryService` definition

**Learning**: Multiple services on one GATT server

---

#### 3.5 Update Connection Task for Battery Notifications

**src/tasks/ble.rs** - connection_task():
```rust
// Add battery signal to select
select3(
    gatt_server.next(),
    JOYSTICK_SIGNAL.wait(),
    BATTERY_SIGNAL.wait(),
).await;

// Handle battery update
let battery_level = BATTERY_SIGNAL.wait().await;
if let Err(e) = battery_service.battery_level_notify(&conn, &battery_level) {
    defmt::warn!("Failed to notify battery level: {}", e);
}
```

**Files to Modify**:
- `src/tasks/ble.rs` - Extend connection task

**Learning**:
- `select3()` for three concurrent futures
- Service handle management

---

#### 3.6 Testing Plan

**nRF Connect Test**:
1. Connect to "microbit-joy"
2. Should see TWO services:
   - Custom Joystick Service (UUID: 12345678...)
   - Battery Service (UUID: 0x180F)
3. Expand Battery Service
4. Should see Battery Level characteristic (UUID: 0x2A19)
5. Enable notifications
6. Should update every 60 seconds

**Python Test**: Extend test_buttons.py
```python
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# Discover service
battery_service = client.services.get_service(BATTERY_SERVICE_UUID)
battery_char = battery_service.get_characteristic(BATTERY_LEVEL_UUID)

# Read initial value
level = await client.read_gatt_char(battery_char)
print(f"Battery Level: {level[0]}%")
```

**Verification Checklist**:
- [ ] Battery Service appears in GATT scan
- [ ] Battery Level reads 0-100%
- [ ] Value makes sense for power source (USB ~100%, battery varies)
- [ ] Notifications work
- [ ] Code compiles without warnings

---

## Phase 4: Add Configurable Settings via GATT

**Learning Objectives**:
- Implement WRITE characteristics
- Handle configuration updates dynamically
- Use READ + WRITE + NOTIFY characteristics
- Validate and sanitize BLE input data
- Store runtime configuration

### Implementation Steps

#### 4.1 Define Configuration Service

**Goal**: Allow BLE clients to configure device behavior

**src/gatt.rs**: Add new service
```rust
/// Configuration Service for Runtime Settings
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcde00")]
pub struct ConfigService {
    /// Joystick update rate (milliseconds): 10-1000ms
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcde01", read, write, notify)]
    pub update_rate_ms: u16,

    /// Device name (max 20 bytes UTF-8)
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcde02", read, write, notify)]
    pub device_name: [u8; 20],

    /// LED blink enable: 0=off, 1=on
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcde03", read, write, notify)]
    pub led_enabled: u8,
}
```

**Files to Create/Modify**:
- `src/gatt.rs` - Add ConfigService

**Learning**: WRITE characteristic implementation in TrouBLE

---

#### 4.2 Create Configuration Data Structure

**Goal**: Shared state for runtime configuration

**src/lib.rs** or **src/gatt.rs**:
```rust
use embassy_sync::signal::Signal;
use embassy_sync::mutex::Mutex;

/// Runtime configuration state
pub struct Config {
    pub joystick_update_ms: u16,
    pub device_name: heapless::String<20>,
    pub led_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            joystick_update_ms: 100,
            device_name: heapless::String::from("microbit-joy"),
            led_enabled: true,
        }
    }
}

pub static CONFIG: Mutex<ThreadModeRawMutex, Config> = Mutex::new(Config::default());
```

**Learning**:
- `heapless::String<N>` for fixed-size strings without heap
- `Mutex` for thread-safe shared state
- `static` initialization

---

#### 4.3 Handle WRITE Events in Connection Task

**Goal**: React to client writes and update configuration

**src/tasks/ble.rs** - connection_task():
```rust
loop {
    match select(gatt_server.next(), JOYSTICK_SIGNAL.wait()).await {
        Either::First(event) => {
            match event {
                GattEvent::Write { handle, data } => {
                    // Identify which characteristic was written
                    if handle == config_service.update_rate_ms_handle() {
                        let new_rate = u16::from_le_bytes([data[0], data[1]]);

                        // Validate range (10-1000ms)
                        if new_rate >= 10 && new_rate <= 1000 {
                            let mut config = CONFIG.lock().await;
                            config.joystick_update_ms = new_rate;

                            defmt::info!("Update rate changed to {}ms", new_rate);

                            // Notify other clients of the change
                            config_service.update_rate_ms_notify(&conn, &new_rate)?;
                        } else {
                            defmt::warn!("Invalid update rate: {}", new_rate);
                        }
                    }
                    // Handle other writable characteristics...
                }
                // Other events...
            }
        }
        Either::Second(joystick_data) => {
            // Existing joystick update logic...
        }
    }
}
```

**Files to Modify**:
- `src/tasks/ble.rs` - Add GattEvent::Write handling

**Learning**:
- GATT event handling
- Characteristic handle comparison
- Input validation
- Notify-on-write pattern

---

#### 4.4 Apply Configuration Changes Dynamically

**Challenge**: Tasks are already running with fixed timing

**Solution Options**:

**Option A**: Restart tasks (complex)
**Option B**: Use dynamic timer (simpler)

**src/tasks/joystick.rs** - Update joystick_read_task:
```rust
#[embassy_executor::task]
pub async fn joystick_read_task(/* params */) {
    // ... calibration ...

    loop {
        // Read joystick...
        // Update signal...

        // Dynamic delay based on config
        let delay = {
            let config = CONFIG.lock().await;
            config.joystick_update_ms
        };
        Timer::after_millis(delay as u64).await;
    }
}
```

**src/tasks/led.rs** - Update led_blink_task:
```rust
#[embassy_executor::task]
pub async fn led_blink_task(mut led: /* ... */) {
    // Startup blinks...

    loop {
        let enabled = {
            let config = CONFIG.lock().await;
            config.led_enabled
        };

        if enabled {
            led.set_high();
            Timer::after_millis(500).await;
            led.set_low();
            Timer::after_millis(500).await;
        } else {
            Timer::after_millis(1000).await;  // Still yield
        }
    }
}
```

**Files to Modify**:
- `src/tasks/joystick.rs` - Dynamic update rate
- `src/tasks/led.rs` - Conditional LED blinking

**Learning**:
- Mutex lock scopes (release before await)
- Dynamic timing in async tasks

---

#### 4.5 Handle Device Name Changes

**Challenge**: Device name is set during advertising, can't change while connected

**Solutions**:
1. **Store only**: Save new name, apply on next advertising cycle
2. **Reconnect required**: Disconnect client to trigger re-advertising with new name

**src/tasks/ble.rs** - ble_app_task():
```rust
async fn advertise(peripheral: &Peripheral, config: &Config) {
    let adv_data = [
        0x02, 0x01, AdFlags::LE_GENERAL_DISCOVERABLE.into_bits(),

        // Dynamic name length
        (config.device_name.len() + 1) as u8,
        0x09,  // Complete Local Name
        // Copy name bytes...
    ];

    // Start advertising with dynamic name
}

#[embassy_executor::task]
pub async fn ble_app_task(/* ... */) {
    loop {
        let config = CONFIG.lock().await;
        advertise(&peripheral, &config).await;
        drop(config);  // Release lock

        // Accept connection...
    }
}
```

**Files to Modify**:
- `src/tasks/ble.rs` - Dynamic advertising data

**Learning**:
- Advertisement data encoding
- Reconnect workflows

---

#### 4.6 Testing Plan

**nRF Connect Test**:
1. Connect to device
2. Find Configuration Service
3. Write to update_rate_ms: 0x00FA (250ms in little-endian)
4. Verify joystick updates slow down to 250ms
5. Write to led_enabled: 0x00 (disable)
6. Verify LED stops blinking
7. Write to device_name: "my-joy" (0x6D792D6A6F79)
8. Disconnect and rescan
9. Should advertise as "my-joy"

**Python Test**:
```python
# Write update rate to 500ms
await client.write_gatt_char(update_rate_char, (500).to_bytes(2, 'little'))

# Write LED disable
await client.write_gatt_char(led_char, b'\x00')

# Write device name
await client.write_gatt_char(name_char, b'test-device\x00\x00\x00\x00\x00\x00\x00\x00\x00')
```

**Verification Checklist**:
- [ ] Can write to all three characteristics
- [ ] Invalid values rejected (e.g., update_rate = 5ms)
- [ ] Joystick rate changes dynamically
- [ ] LED can be disabled/enabled
- [ ] Device name changes after reconnect
- [ ] Notifications sent when values change
- [ ] No crashes or panics

---

## Learning Resources

### Rust Embassy Documentation
- **Embassy Book**: https://embassy.dev/book/
- **embassy-nrf API**: https://docs.embassy.dev/embassy-nrf/
- **embassy-executor**: https://docs.embassy.dev/embassy-executor/

### BLE/GATT References
- **Bluetooth SIG Specs**: https://www.bluetooth.com/specifications/specs/
- **GATT Services**: https://www.bluetooth.com/specifications/assigned-numbers/
- Included in repo: `GATT.md`, `BLE_IMPLEMENTATION.md`

### TrouBLE (BLE Stack)
- **TrouBLE GitHub**: https://github.com/embassy-rs/trouble
- **Examples**: Look at embassy-rs/embassy repository
- Macro documentation: In-code examples (this project)

### micro:bit Hardware
- **micro:bit v2 Schematic**: https://tech.microbit.org/hardware/schematic/
- **nRF52833 Datasheet**: https://infocenter.nordicsemi.com/
- Included: `memory.x`, hardware pin assignments

### Testing Tools
- **bleak** (Python BLE): https://bleak.readthedocs.io/
- **Web Bluetooth API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API
- **nRF Connect**: Nordic Semiconductor app (Android/iOS/Desktop)

---

## Development Workflow

### Build and Flash
```bash
cd microbit-ble-dev

# Build only
cargo build --release

# Build and flash
cargo run --release

# Flash with RTT monitoring
cargo embed --release
```

### Monitoring Logs
```bash
# probe-rs already captures defmt logs during cargo run/embed
# Look for defmt::info!, defmt::warn! output in console
```

### Git Workflow
```bash
# After completing Phase 1
git checkout -b phase-1-buttons
git add .
git commit -m "Add Button A/B GATT characteristics

- Add button_a and button_b to JoystickService
- Implement button_read_task with 20ms polling
- Update connection_task to notify button state
- Test with test_buttons.py
"

# Create feature branches for each phase
git checkout -b phase-2-modules
git checkout -b phase-3-battery
git checkout -b phase-4-config
```

---

## Next Steps After These 4 Phases

Once you've completed all four phases, you'll have:
- ✅ Complete joystick with button support
- ✅ Well-organized modular codebase
- ✅ Standard Battery Service implementation
- ✅ Dynamic runtime configuration via GATT

**Suggested Advanced Features**:
1. **HID-over-GATT**: Make it a real Bluetooth gamepad
2. **BLE Security**: Implement pairing and encryption
3. **Multiple Connections**: Support 2-3 simultaneous clients
4. **Power Optimization**: Lower power advertising, sleep modes
5. **Data Logging**: Store joystick movements to flash memory

---

## Support and Help

**Debugging Tips**:
- Use `defmt::info!()` liberally to trace execution
- Check defmt logs for warnings
- Compare against ble-joystick if something breaks
- Read compiler errors carefully (Rust errors are helpful)

**Common Issues**:
- **"error: characteristic not found"**: Check UUID matches
- **"task arena full"**: Increase task-arena-size in Cargo.toml
- **"failed to notify"**: Client might not have enabled notifications
- **Advertising not visible**: Check adv_data encoding, use nRF Connect sniffer

**When Stuck**:
1. Re-read the relevant section in GATT.md or BLE_IMPLEMENTATION.md
2. Look at the original ble-joystick implementation
3. Check TrouBLE examples in embassy repository
4. Add debug logs to understand control flow

---

## Success Criteria

**Phase 1**: Python script shows button presses
**Phase 2**: Code compiles in modular structure, functionality unchanged
**Phase 3**: nRF Connect shows Battery Service with realistic percentage
**Phase 4**: Can change update rate via GATT write, see timing change

**Overall**: You understand:
- How GATT services and characteristics work
- Embassy async task model
- BLE connection lifecycle
- Input validation and error handling
- Embedded Rust project organization

---

**Good luck with your BLE learning journey! Take your time with each phase and experiment freely.**
