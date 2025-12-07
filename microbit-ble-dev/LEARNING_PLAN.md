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

**Task**: Add two new characteristics for buttons to the existing JoystickService

**Files to Modify**:
- `src/main.rs:82-107` - Add button fields to `JoystickService` struct

**References**:
- TrouBLE GATT macro documentation: Look at existing x_axis/y_axis examples
- Test files already reference these UUIDs: `test/test_buttons.py:24-25`

---

#### 1.2 Update Shared Data Structure

**Task**: Add button state fields to JoystickData struct

**Files to Modify**:
- `src/main.rs:109-114` - Extend `JoystickData` struct
- `src/main.rs:232` - Update initialization in `joystick_read_task()`

**Learning**: How async tasks share data via `Signal<ThreadModeRawMutex, T>`

---

#### 1.3 Create Button Reading Task

**Goal**: Create a new Embassy task that reads button states and updates the signal

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

**Task**: Add button notification logic to connection_task

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

**Files to Create**:
- `src/gatt.rs` - New file with service definitions

**Files to Modify**:
- `src/main.rs` - Remove service definitions, add `mod gatt;`

**Learning**: Public API design, re-exporting types

---

#### 2.3 Extract Task Modules

**Goal**: Move each async task to its own module

**Files to Create**:
- `src/tasks/mod.rs`, `src/tasks/led.rs`, `src/tasks/joystick.rs`, `src/tasks/ble.rs`

**Files to Modify**:
- `src/main.rs` - Remove task definitions, add `mod tasks;`

**Learning**: Module privacy, `pub` visibility, static items in modules

---

#### 2.4 Create Shared Library Module

**Goal**: Centralize constants and shared types

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

**Files to Modify**:
- `src/gatt.rs` - Add BatteryService definition

**Learning**:
- TrouBLE supports both 16-bit and 128-bit UUIDs
- Standard services improve compatibility with generic BLE apps

---

#### 3.3 Calculate Battery Level from VDD

**micro:bit v2 Power**:
- Powered by USB (5V) or battery pack (2x AAA = 3V)
- nRF52833 VDD range: 1.7V - 3.6V
- Internal voltage: Accessible via SAADC channel VDD with 1/6 prescaler

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

**Files to Modify**:
- `src/tasks/ble.rs` - Update server builder
- `src/gatt.rs` - Add `BatteryService` definition

**Learning**: Multiple services on one GATT server

---

#### 3.5 Update Connection Task for Battery Notifications

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

**Files to Create/Modify**:
- `src/gatt.rs` - Add ConfigService

**Learning**: WRITE characteristic implementation in TrouBLE

---

#### 4.2 Create Configuration Data Structure

**Goal**: Shared state for runtime configuration

**Learning**:
- `heapless::String<N>` for fixed-size strings without heap
- `Mutex` for thread-safe shared state
- `static` initialization

---

#### 4.3 Handle WRITE Events in Connection Task

**Goal**: React to client writes and update configuration

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
- **Option A**: Restart tasks (complex)
- **Option B**: Use dynamic timer (simpler)

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
