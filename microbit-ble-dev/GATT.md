# GATT (Generic Attribute Profile) Guide

Complete guide to understanding and extending the BLE GATT implementation in this project.

## Table of Contents

1. [GATT Fundamentals](#gatt-fundamentals)
2. [Current Implementation](#current-implementation)
3. [Adding More Characteristics](#adding-more-characteristics)
4. [HID-over-GATT Implementation](#hid-over-gatt-implementation)
5. [Testing GATT Services](#testing-gatt-services)
6. [Troubleshooting](#troubleshooting)

---

## GATT Fundamentals

### What is GATT?

**GATT** (Generic Attribute Profile) is the protocol that defines how BLE devices structure and exchange data. It's built on top of the **ATT** (Attribute Protocol) and provides a hierarchical data structure.

### GATT Hierarchy

```
┌─────────────────────────────────────────────────┐
│              GATT Server                         │
│  (Your micro:bit)                               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ Service (UUID: ...def0)                  │  │
│  │ "Joystick Service"                       │  │
│  ├──────────────────────────────────────────┤  │
│  │                                          │  │
│  │  ┌────────────────────────────────────┐ │  │
│  │  │ Characteristic (UUID: ...def1)     │ │  │
│  │  │ "X-Axis"                           │ │  │
│  │  │ • Value: u16 (0-1023)              │ │  │
│  │  │ • Properties: READ, NOTIFY         │ │  │
│  │  │ • Descriptors: (optional)          │ │  │
│  │  └────────────────────────────────────┘ │  │
│  │                                          │  │
│  │  ┌────────────────────────────────────┐ │  │
│  │  │ Characteristic (UUID: ...def2)     │ │  │
│  │  │ "Y-Axis"                           │ │  │
│  │  │ • Value: u16 (0-1023)              │ │  │
│  │  │ • Properties: READ, NOTIFY         │ │  │
│  │  └────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ Service (UUID: 0x180F)                   │  │
│  │ "Battery Service" (Standard)             │  │
│  │  └─ Characteristic: Battery Level       │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Key Concepts

#### 1. Service
- **Purpose**: Logical grouping of related characteristics
- **UUID**: 128-bit (custom) or 16-bit (standard Bluetooth SIG)
- **Example**: Device Information Service (0x180A), Battery Service (0x180F)

#### 2. Characteristic
- **Purpose**: Individual data point that can be read, written, or notified
- **UUID**: Unique identifier within service
- **Value**: Actual data (bytes)
- **Properties**: Define allowed operations

#### 3. Properties
| Property | Direction | Description | Use Case |
|----------|-----------|-------------|----------|
| **READ** | Client → Server | Client requests current value | Get joystick position on demand |
| **WRITE** | Client → Server | Client updates value | Set LED brightness |
| **WRITE_WITHOUT_RESPONSE** | Client → Server | Write without ACK | Fast commands |
| **NOTIFY** | Server → Client | Server pushes updates (subscription) | Real-time joystick updates |
| **INDICATE** | Server → Client | Like notify but with ACK | Critical alerts |
| **BROADCAST** | Server → World | Advertise value | Beacon data |

#### 4. Descriptors (Optional)
- **CCCD** (Client Characteristic Configuration Descriptor): Enable/disable notifications
- **User Description**: Human-readable name
- **Presentation Format**: Data type and units

### UUID Format

**128-bit Custom UUID**:
```
12345678-1234-5678-1234-56789abcdef0
│      │ │  │ │  │ │  │           │
└──────┴─┴──┴─┴──┴─┴──┴───────────┘
   Base UUID (you define)
```

**16-bit Standard UUID** (Bluetooth SIG assigned):
```
0x180F → Battery Service
0x2A19 → Battery Level Characteristic
```

Converted to 128-bit:
```
0000180F-0000-1000-8000-00805F9B34FB
```

---

## Current Implementation

### Code Structure (src/main.rs:30-44)

```rust
// BLE GATT Server definition
#[gatt_server]
struct JoystickServer {
    joystick_service: JoystickService,
}

// Custom Joystick Service
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,
}
```

### What the Macros Generate

The `#[gatt_server]` and `#[gatt_service]` macros generate code for:

1. **Service Registration**: Adds service to GATT attribute table
2. **Characteristic Handles**: Creates methods to access characteristics
3. **Property Implementation**: Handles read/write/notify operations
4. **UUID Management**: Converts strings to UUID types

**Generated methods** (conceptual):
```rust
impl JoystickService {
    fn x_axis(&self) -> CharacteristicHandle<u16> { ... }
    fn y_axis(&self) -> CharacteristicHandle<u16> { ... }
}

// Usage:
let x_char = server.joystick_service.x_axis;
x_char.set(server, &512);           // Update value
x_char.notify(conn, &512).await;    // Send notification
```

### Data Flow

```
┌─────────────────────────────────────────────────┐
│  1. Joystick ADC Task                           │
│     • Reads analog values (10 Hz)               │
│     • Converts to 0-1023 range                  │
│     • JOYSTICK_SIGNAL.signal(data)              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  2. Connection Task (select loop)               │
│     • JOYSTICK_SIGNAL.wait() → new data         │
│     • x_char.set(server, &data.x)               │
│     • x_char.notify(conn, &data.x).await        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  3. BLE Stack (trouble-host)                    │
│     • Queues notification packet                │
│     • Waits for next connection interval        │
│     • Transmits over radio                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  4. Connected Client                            │
│     • Receives notification (~30ms interval)    │
│     • Updates UI or game controller mapping     │
└─────────────────────────────────────────────────┘
```

### Current Service Specification

| Element | UUID | Type | Properties | Description |
|---------|------|------|------------|-------------|
| **Service** | `12345678-...def0` | - | - | Joystick Service |
| X-Axis | `12345678-...def1` | u16 | READ, NOTIFY | Horizontal position (0-1023) |
| Y-Axis | `12345678-...def2` | u16 | READ, NOTIFY | Vertical position (0-1023) |

---

## Adding More Characteristics

### Example 1: Adding Button Support

Let's add two buttons (A and B) to the joystick service.

#### Step 1: Update the Service Definition

```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,

    // NEW: Button A state
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    button_a: u8,  // 0 = released, 1 = pressed

    // NEW: Button B state
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,
}
```

#### Step 2: Update Data Structure

```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,
    y: u16,
    button_a: u8,  // NEW
    button_b: u8,  // NEW
}
```

#### Step 3: Create Button Reading Task

```rust
#[embassy_executor::task]
async fn button_read_task(
    button_a: embassy_nrf::gpio::Input<'static>,
    button_b: embassy_nrf::gpio::Input<'static>,
) {
    use embassy_nrf::gpio::Pull;

    // Configure buttons with pull-up resistors
    let mut btn_a = button_a;
    let mut btn_b = button_b;

    loop {
        // Wait for button press (interrupt-driven)
        btn_a.wait_for_any_edge().await;
        btn_b.wait_for_any_edge().await;

        // Read current button states
        let a_pressed = !btn_a.is_high();  // Active low
        let b_pressed = !btn_b.is_high();

        info!("Buttons: A={}, B={}", a_pressed, b_pressed);

        // TODO: Combine with joystick data and signal
        // (see combined approach below)

        Timer::after(Duration::from_millis(10)).await; // Debounce
    }
}
```

#### Step 4: Combine Button and Joystick Data

**Option A: Separate Signals** (simple but inefficient)
```rust
static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, (u16, u16)> = Signal::new();
static BUTTON_SIGNAL: Signal<ThreadModeRawMutex, (u8, u8)> = Signal::new();

// In connection task
loop {
    let joystick_future = JOYSTICK_SIGNAL.wait();
    let button_future = BUTTON_SIGNAL.wait();
    let gatt_future = conn.next();

    match select3(joystick_future, button_future, gatt_future).await {
        // Handle each case
    }
}
```

**Option B: Single Combined Signal** (recommended)
```rust
static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();

// Joystick task reads buttons too
#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
    button_a: embassy_nrf::gpio::Input<'static>,
    button_b: embassy_nrf::gpio::Input<'static>,
) {
    // ... ADC setup ...

    loop {
        adc.sample(&mut buf).await;

        // Read buttons
        let a_pressed = !button_a.is_high() as u8;
        let b_pressed = !button_b.is_high() as u8;

        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: a_pressed,
            button_b: b_pressed,
        };

        JOYSTICK_SIGNAL.signal(joystick_data);
        Timer::after(Duration::from_millis(100)).await;
    }
}
```

#### Step 5: Update Notification Logic

```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;  // NEW
    let btn_b_char = server.joystick_service.button_b;  // NEW

    // Initialize all characteristics
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);  // NEW
    let _ = btn_b_char.set(server, &0);  // NEW

    loop {
        let gatt_event_future = conn.next();
        let joystick_update_future = JOYSTICK_SIGNAL.wait();

        match select(gatt_event_future, joystick_update_future).await {
            // ... GATT event handling ...

            embassy_futures::select::Either::Second(data) => {
                // Update all characteristics
                let _ = x_char.set(server, &data.x);
                let _ = y_char.set(server, &data.y);
                let _ = btn_a_char.set(server, &data.button_a);  // NEW
                let _ = btn_b_char.set(server, &data.button_b);  // NEW

                // Send notifications
                let _ = x_char.notify(conn, &data.x).await;
                let _ = y_char.notify(conn, &data.y).await;
                let _ = btn_a_char.notify(conn, &data.button_a).await;  // NEW
                let _ = btn_b_char.notify(conn, &data.button_b).await;  // NEW
            }
        }
    }
}
```

#### Step 6: Update main() to Spawn Button Task

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let board = Microbit::new(Config::default());

    // Configure button pins
    let button_a = embassy_nrf::gpio::Input::new(
        board.p5,  // Adjust pin based on hardware
        embassy_nrf::gpio::Pull::Up,
    );

    let button_b = embassy_nrf::gpio::Input::new(
        board.p11,  // Adjust pin based on hardware
        embassy_nrf::gpio::Pull::Up,
    );

    // Spawn joystick task with button pins
    spawner.must_spawn(joystick_read_task(
        board.saadc,
        board.p1,
        board.p2,
        button_a,
        button_b,
    ));

    // ... rest of main ...
}
```

### Example 2: Adding Battery Level

Standard Battery Service (0x180F) with Battery Level characteristic (0x2A19).

```rust
#[gatt_server]
struct JoystickServer {
    joystick_service: JoystickService,
    battery_service: BatteryService,  // NEW
}

// Standard Battery Service
#[gatt_service(uuid = "0000180F-0000-1000-8000-00805F9B34FB")]
struct BatteryService {
    #[characteristic(uuid = "00002A19-0000-1000-8000-00805F9B34FB", read, notify)]
    battery_level: u8,  // 0-100 percentage
}
```

**Reading battery level** (if micro:bit has battery sensing):
```rust
#[embassy_executor::task]
async fn battery_monitor_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    vdd_pin: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_XX>,
) {
    // Configure ADC for battery voltage measurement
    let mut adc = Saadc::new(saadc, Irqs, Config::default(), [
        ChannelConfig::single_ended(vdd_pin),
    ]);

    loop {
        let mut buf = [0i16; 1];
        adc.sample(&mut buf).await;

        // Convert ADC reading to percentage (0-100)
        // Assumes 3.3V = 100%, 2.0V = 0%
        let voltage = (buf[0] as f32 / 4096.0) * 3.3;
        let percentage = ((voltage - 2.0) / 1.3 * 100.0).clamp(0.0, 100.0) as u8;

        BATTERY_SIGNAL.signal(percentage);

        // Check every 60 seconds
        Timer::after(Duration::from_secs(60)).await;
    }
}
```

### Example 3: Adding Configuration Characteristic

Allow client to configure sample rate via WRITE property.

```rust
#[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef5", read, write)]
sample_rate_ms: u16,  // Configurable sample rate (10-1000ms)
```

**Handling writes** in connection task:
```rust
GattConnectionEvent::Gatt { event } => {
    // Check if this is a write to sample_rate
    if event.is_write_to(server.joystick_service.sample_rate_ms) {
        let new_rate = event.data_as::<u16>();
        if new_rate >= 10 && new_rate <= 1000 {
            SAMPLE_RATE_SIGNAL.signal(new_rate);
            info!("Sample rate updated to {}ms", new_rate);
        }
    }

    match event.accept() {
        Ok(reply) => reply.send().await,
        Err(e) => warn!("[BLE] Error: {:?}", e),
    }
}
```

---

## HID-over-GATT Implementation

### What is HID-over-GATT?

**HID** (Human Interface Device) over GATT allows your micro:bit to appear as a standard **gamepad/joystick** to phones, tablets, and computers. No custom app needed!

### Benefits

- ✅ Works with any device (Windows, macOS, Linux, Android, iOS)
- ✅ No custom client app required
- ✅ Standard gamepad mappings
- ✅ Works with games and emulators directly
- ❌ More complex to implement
- ❌ Larger code size (~20KB additional)

### HID Service Structure

```
HID Service (UUID: 0x1812)
├── HID Information (0x2A4A)
│   └── Version, country code, flags
├── Report Map (0x2A4B)
│   └── HID descriptor (defines report format)
├── HID Control Point (0x2A4C)
│   └── Suspend/resume commands
├── Protocol Mode (0x2A4E)
│   └── Boot/report mode
└── Report (0x2A4D) - Multiple instances
    ├── Input Report: Device → Host (joystick data)
    ├── Output Report: Host → Device (LEDs, rumble)
    └── Feature Report: Bidirectional (config)
```

### HID Report Descriptor

The **Report Map** describes the data format. For a gamepad:

```c
// Gamepad Report Descriptor (example)
const uint8_t HID_REPORT_MAP[] = {
    0x05, 0x01,        // USAGE_PAGE (Generic Desktop)
    0x09, 0x05,        // USAGE (Game Pad)
    0xa1, 0x01,        // COLLECTION (Application)

    // Two 8-bit axes (X and Y)
    0x05, 0x01,        //   USAGE_PAGE (Generic Desktop)
    0x09, 0x30,        //   USAGE (X)
    0x09, 0x31,        //   USAGE (Y)
    0x15, 0x00,        //   LOGICAL_MINIMUM (0)
    0x26, 0xff, 0x03,  //   LOGICAL_MAXIMUM (1023)
    0x75, 0x10,        //   REPORT_SIZE (16 bits)
    0x95, 0x02,        //   REPORT_COUNT (2)
    0x81, 0x02,        //   INPUT (Data, Variable, Absolute)

    // Buttons (8 buttons)
    0x05, 0x09,        //   USAGE_PAGE (Button)
    0x19, 0x01,        //   USAGE_MINIMUM (Button 1)
    0x29, 0x08,        //   USAGE_MAXIMUM (Button 8)
    0x15, 0x00,        //   LOGICAL_MINIMUM (0)
    0x25, 0x01,        //   LOGICAL_MAXIMUM (1)
    0x75, 0x01,        //   REPORT_SIZE (1 bit)
    0x95, 0x08,        //   REPORT_COUNT (8)
    0x81, 0x02,        //   INPUT (Data, Variable, Absolute)

    0xc0               // END_COLLECTION
};
```

### Implementation with TrouBLE

**Step 1: Add HID Service Definition**

```rust
use trouble_host::hid::*;

#[gatt_server]
struct JoystickServer {
    hid_service: HidService,
}

#[gatt_service(uuid = "00001812-0000-1000-8000-00805F9B34FB")]  // HID Service
struct HidService {
    // HID Information (read-only)
    #[characteristic(uuid = "00002A4A-0000-1000-8000-00805F9B34FB", read)]
    hid_info: [u8; 4],  // [version_lo, version_hi, country_code, flags]

    // Report Map (read-only)
    #[characteristic(uuid = "00002A4B-0000-1000-8000-00805F9B34FB", read)]
    report_map: &'static [u8],

    // HID Control Point (write without response)
    #[characteristic(uuid = "00002A4C-0000-1000-8000-00805F9B34FB", write_without_response)]
    control_point: u8,

    // Protocol Mode (read, write without response)
    #[characteristic(uuid = "00002A4E-0000-1000-8000-00805F9B34FB", read, write_without_response)]
    protocol_mode: u8,  // 0 = boot, 1 = report

    // Input Report (read, notify)
    #[characteristic(uuid = "00002A4D-0000-1000-8000-00805F9B34FB", read, notify)]
    input_report: [u8; 5],  // [x_lo, x_hi, y_lo, y_hi, buttons]
}
```

**Step 2: Initialize HID Service**

```rust
static HID_REPORT_DESCRIPTOR: &[u8] = &[
    0x05, 0x01,        // USAGE_PAGE (Generic Desktop)
    0x09, 0x05,        // USAGE (Game Pad)
    0xa1, 0x01,        // COLLECTION (Application)
    // ... (full descriptor from above)
    0xc0               // END_COLLECTION
];

async fn ble_app_task<C: Controller>(
    mut peripheral: Peripheral<'_, C, DefaultPacketPool>,
) {
    let server = JoystickServer::new_with_config(GapConfig::Peripheral(PeripheralConfig {
        name: "micro:bit Gamepad",
        appearance: &appearance::hid::GAMEPAD,  // Important: HID appearance
    }))
    .expect("Failed to create GATT server");

    // Initialize HID characteristics
    server.hid_service.hid_info.set(&[0x11, 0x01, 0x00, 0x02]);  // HID v1.11, no country, normally connectable
    server.hid_service.report_map.set(HID_REPORT_DESCRIPTOR);
    server.hid_service.protocol_mode.set(&1);  // Report mode

    // ... advertising and connection handling ...
}
```

**Step 3: Send HID Reports**

```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let input_report_char = server.hid_service.input_report;

    loop {
        let joystick_update_future = JOYSTICK_SIGNAL.wait();
        let gatt_event_future = conn.next();

        match select(joystick_update_future, gatt_event_future).await {
            embassy_futures::select::Either::First(data) => {
                // Pack data into HID report format
                let report = [
                    (data.x & 0xFF) as u8,        // X low byte
                    ((data.x >> 8) & 0xFF) as u8, // X high byte
                    (data.y & 0xFF) as u8,        // Y low byte
                    ((data.y >> 8) & 0xFF) as u8, // Y high byte
                    (data.button_a | (data.button_b << 1)),  // Buttons packed
                ];

                // Send HID input report
                let _ = input_report_char.set(server, &report);
                let _ = input_report_char.notify(conn, &report).await;
            }

            embassy_futures::select::Either::Second(event) => {
                match event {
                    GattConnectionEvent::Disconnected { reason } => {
                        info!("[HID] Disconnected: {:?}", reason);
                        break;
                    }
                    GattConnectionEvent::Gatt { event } => {
                        // Handle control point writes (suspend/resume)
                        match event.accept() {
                            Ok(reply) => reply.send().await,
                            Err(e) => warn!("[HID] Error: {:?}", e),
                        }
                    }
                    _ => {}
                }
            }
        }
    }
}
```

**Step 4: Update Advertising Data**

```rust
async fn advertise<'a, 'b, C: Controller>(
    name: &'a str,
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, BleHostError<C::Error>> {
    let mut advertiser_data = [0; 31];
    AdStructure::encode_slice(
        &[
            AdStructure::Flags(LE_GENERAL_DISCOVERABLE | BR_EDR_NOT_SUPPORTED),
            AdStructure::CompleteLocalName(name.as_bytes()),
            AdStructure::CompleteListOf16BitServiceUuids(&[0x1812]),  // HID Service
            // Appearance: Gamepad (964 = 0x03C4)
            AdStructure::Appearance(964),
        ],
        &mut advertiser_data[..],
    )?;

    // ... rest of advertising ...
}
```

### Complete HID Report Format Example

For a **dual-stick gamepad with 8 buttons**:

```rust
#[repr(C, packed)]
struct HidGamepadReport {
    x_left: u16,      // Left stick X (0-1023)
    y_left: u16,      // Left stick Y (0-1023)
    x_right: u16,     // Right stick X (0-1023)
    y_right: u16,     // Right stick Y (0-1023)
    buttons: u8,      // 8 buttons (bit field)
}

// Usage:
let report = HidGamepadReport {
    x_left: data.x,
    y_left: data.y,
    x_right: 512,     // Center (no second stick)
    y_right: 512,
    buttons: (data.button_a as u8) | ((data.button_b as u8) << 1),
};

let bytes = unsafe {
    core::slice::from_raw_parts(
        &report as *const _ as *const u8,
        core::mem::size_of::<HidGamepadReport>()
    )
};

input_report_char.notify(conn, bytes).await;
```

### Testing HID-over-GATT

**Windows**:
1. Settings → Bluetooth & devices → Add device
2. Select "micro:bit Gamepad"
3. Open "Set up USB game controllers" (joy.cpl)
4. Should appear as "Bluetooth HID Device"

**Linux**:
```bash
# Test with jstest
sudo apt install joystick
jstest /dev/input/js0

# Or with evtest
sudo evtest
# Select the micro:bit gamepad device
```

**macOS**:
1. System Settings → Bluetooth
2. Connect to "micro:bit Gamepad"
3. Test with "Enjoyable" app or game that supports gamepads

**Android/iOS**:
- Should work automatically with gamepad-compatible apps
- Test with "Gamepad Tester" app

### Advantages of HID vs Custom GATT

| Feature | Custom GATT | HID-over-GATT |
|---------|-------------|---------------|
| **Compatibility** | Requires custom app | Works everywhere |
| **Setup** | Must install app | Plug and play |
| **Flexibility** | Any data format | Fixed HID reports |
| **Code Size** | Smaller (~10KB) | Larger (~30KB) |
| **Latency** | ~50ms typical | ~30ms typical |
| **Debugging** | Easy (custom tools) | Harder (HID tools) |
| **Use Case** | Custom applications | Gaming, standard input |

---

## Testing GATT Services

### Method 1: Web Bluetooth API

**HTML Test Page** (ble-test.html):
```html
<!DOCTYPE html>
<html>
<head>
    <title>GATT Service Tester</title>
</head>
<body>
    <button id="connect">Connect to micro:bit</button>
    <div id="status"></div>
    <pre id="data"></pre>

    <script>
        const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
        const X_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1';
        const Y_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef2';
        const BTN_A_UUID = '12345678-1234-5678-1234-56789abcdef3';
        const BTN_B_UUID = '12345678-1234-5678-1234-56789abcdef4';

        document.getElementById('connect').addEventListener('click', async () => {
            try {
                // Request device
                const device = await navigator.bluetooth.requestDevice({
                    filters: [{ name: 'microbit-joy' }],
                    optionalServices: [SERVICE_UUID]
                });

                // Connect to GATT server
                const server = await device.gatt.connect();
                const service = await server.getPrimaryService(SERVICE_UUID);

                // Get characteristics
                const xChar = await service.getCharacteristic(X_CHAR_UUID);
                const yChar = await service.getCharacteristic(Y_CHAR_UUID);
                const btnAChar = await service.getCharacteristic(BTN_A_UUID);
                const btnBChar = await service.getCharacteristic(BTN_B_UUID);

                // Read initial values
                const xValue = await xChar.readValue();
                const yValue = await yChar.readValue();
                console.log('Initial X:', xValue.getUint16(0, true));
                console.log('Initial Y:', yValue.getUint16(0, true));

                // Subscribe to notifications
                xChar.addEventListener('characteristicvaluechanged', (e) => {
                    const x = e.target.value.getUint16(0, true);
                    document.getElementById('data').textContent = `X: ${x}`;
                });
                await xChar.startNotifications();

                yChar.addEventListener('characteristicvaluechanged', (e) => {
                    const y = e.target.value.getUint16(0, true);
                    document.getElementById('data').textContent += `\nY: ${y}`;
                });
                await yChar.startNotifications();

                btnAChar.addEventListener('characteristicvaluechanged', (e) => {
                    const a = e.target.value.getUint8(0);
                    document.getElementById('data').textContent += `\nButton A: ${a ? 'PRESSED' : 'RELEASED'}`;
                });
                await btnAChar.startNotifications();

                btnBChar.addEventListener('characteristicvaluechanged', (e) => {
                    const b = e.target.value.getUint8(0);
                    document.getElementById('data').textContent += `\nButton B: ${b ? 'PRESSED' : 'RELEASED'}`;
                });
                await btnBChar.startNotifications();

                document.getElementById('status').textContent = 'Connected!';
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('status').textContent = 'Error: ' + error.message;
            }
        });
    </script>
</body>
</html>
```

### Method 2: Python (Bleak)

```python
#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"

def notification_handler(sender, data):
    """Handle BLE notifications"""
    if sender.uuid == X_CHAR_UUID:
        x = int.from_bytes(data, byteorder='little', signed=False)
        print(f"X: {x:4d}", end='  ')
    elif sender.uuid == Y_CHAR_UUID:
        y = int.from_bytes(data, byteorder='little', signed=False)
        print(f"Y: {y:4d}", end='  ')
    elif sender.uuid == BTN_A_UUID:
        print(f"A: {'PRESS' if data[0] else 'REL'}", end='  ')
    elif sender.uuid == BTN_B_UUID:
        print(f"B: {'PRESS' if data[0] else 'REL'}", end='\n')

async def main():
    # Find device
    print("Scanning for microbit-joy...")
    device = await BleakScanner.find_device_by_name("microbit-joy")

    if not device:
        print("Device not found!")
        return

    print(f"Found device: {device.address}")

    # Connect
    async with BleakClient(device) as client:
        print(f"Connected: {client.is_connected}")

        # Read initial values
        x_initial = await client.read_gatt_char(X_CHAR_UUID)
        y_initial = await client.read_gatt_char(Y_CHAR_UUID)
        print(f"Initial X: {int.from_bytes(x_initial, 'little')}")
        print(f"Initial Y: {int.from_bytes(y_initial, 'little')}")

        # Subscribe to notifications
        await client.start_notify(X_CHAR_UUID, notification_handler)
        await client.start_notify(Y_CHAR_UUID, notification_handler)
        await client.start_notify(BTN_A_UUID, notification_handler)
        await client.start_notify(BTN_B_UUID, notification_handler)

        print("\nReceiving notifications (Ctrl+C to stop)...")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Method 3: bluetoothctl (Linux)

```bash
bluetoothctl

# Scan and connect
scan on
# Wait for device to appear
connect C9:10:1E:E3:5A:41

# View GATT attributes
menu gatt
list-attributes

# Read characteristic
select-attribute /org/bluez/hci0/dev_C9_10_1E_E3_5A_41/service000a/char000b
read

# Enable notifications
notify on
```

### Method 4: nRF Connect (Mobile)

1. Open nRF Connect app (Android/iOS)
2. Scan for "microbit-joy"
3. Tap "Connect"
4. Expand "Unknown Service" (shows your UUID)
5. Tap ↓ icon on characteristics to read
6. Tap 🔔 icon to enable notifications
7. Move joystick and press buttons to see updates

---

## Troubleshooting

### Issue 1: Service Not Visible

**Symptoms**: Client can't see your custom service

**Causes**:
1. Service not advertised in advertisement data
2. Client not requesting optional services
3. GATT server initialization failed

**Solutions**:
```rust
// 1. Add service UUID to advertisement
AdStructure::CompleteListOf128BitServiceUuids(&[
    &uuid_bytes_from_string("12345678-1234-5678-1234-56789abcdef0")
])

// 2. In Web Bluetooth, add to optionalServices
navigator.bluetooth.requestDevice({
    optionalServices: ['12345678-1234-5678-1234-56789abcdef0']
})

// 3. Check logs for GATT server creation
info!("[BLE] Creating GATT server...");
let server = JoystickServer::new_with_config(...).expect("Failed to create GATT server");
info!("[BLE] GATT server created");
```

### Issue 2: Notifications Not Received

**Symptoms**: Can read characteristic but don't receive notifications

**Causes**:
1. Client hasn't enabled notifications
2. CCCD (Client Characteristic Configuration Descriptor) not written
3. Connection interval too slow

**Solutions**:
```javascript
// Enable notifications properly
const char = await service.getCharacteristic(X_CHAR_UUID);
char.addEventListener('characteristicvaluechanged', handler);
await char.startNotifications();  // This writes to CCCD
```

**Debug in Rust**:
```rust
match x_char.notify(conn, &data.x).await {
    Ok(_) => { /* notification sent */ },
    Err(e) => error!("Notification failed: {:?}", e),
}
```

### Issue 3: Connection Drops Frequently

**Causes**:
1. Weak signal (distance/obstacles)
2. Connection interval too aggressive
3. Supervision timeout too short
4. Radio interference

**Solutions**:
```rust
// Adjust connection parameters
let conn_params = ConnectionParameters {
    interval_min: Duration::from_millis(20),    // Default: 7.5ms
    interval_max: Duration::from_millis(40),    // Default: 4000ms
    slave_latency: 0,
    supervision_timeout: Duration::from_secs(5), // Default: 10s
};
```

### Issue 4: High Latency

**Causes**:
1. Slow sample rate (100ms default)
2. Long connection interval
3. Multiple notifications per interval

**Solutions**:
```rust
// Increase sample rate
Timer::after(Duration::from_millis(50)).await;  // 20 Hz

// Request faster connection interval (client-side)
// Most clients negotiate 15-30ms automatically
```

### Issue 5: Memory Issues

**Symptoms**: Build fails with "out of memory" or runtime crashes

**Solutions**:
```toml
# Increase task arena size
[dependencies]
embassy-executor = { version = "0.7.0", features = [
    "task-arena-size-65536"  # Increase from 32768
] }
```

```rust
// Reduce buffer sizes
const CONNECTIONS_MAX: usize = 1;  // Only 1 connection
const L2CAP_CHANNELS_MAX: usize = 2;  // Minimum needed
```

### Issue 6: UUID Format Errors

**Symptoms**: Compile error with UUID string

**Common mistakes**:
```rust
// ❌ Wrong: 16-bit UUID as 128-bit
#[gatt_service(uuid = "180F")]

// ✅ Correct: Full 128-bit UUID
#[gatt_service(uuid = "0000180F-0000-1000-8000-00805F9B34FB")]

// ❌ Wrong: Missing hyphens
#[gatt_service(uuid = "123456781234567812345678abcdef0")]

// ✅ Correct: Proper format
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
```

---

## Best Practices

### 1. UUID Management

**Use a consistent base UUID**:
```
Base: 12345678-1234-5678-1234-56789abcde00

Service:  12345678-1234-5678-1234-56789abcdef0
X-Axis:   12345678-1234-5678-1234-56789abcdef1
Y-Axis:   12345678-1234-5678-1234-56789abcdef2
Button A: 12345678-1234-5678-1234-56789abcdef3
...
```

**Generate unique base UUID**:
```bash
# Linux/macOS
uuidgen

# Or use online generator
# https://www.uuidgenerator.net/
```

### 2. Characteristic Design

**Do**: Use appropriate data types
```rust
u8:  0-255 (buttons, percentages)
u16: 0-65535 (joystick axes, sensor values)
i16: -32768 to 32767 (temperature, accelerometer)
```

**Don't**: Overuse notifications
```rust
// ❌ Bad: Notify every 1ms (floods connection)
Timer::after(Duration::from_millis(1)).await;

// ✅ Good: 10-20 Hz is usually enough
Timer::after(Duration::from_millis(50)).await;
```

### 3. Error Handling

**Always log GATT errors**:
```rust
match x_char.set(server, &data.x) {
    Ok(_) => {},
    Err(e) => error!("Failed to set characteristic: {:?}", e),
}
```

### 4. Power Efficiency

**Reduce notification frequency when possible**:
```rust
// Only notify if value changed significantly
if (new_value - old_value).abs() > THRESHOLD {
    x_char.notify(conn, &new_value).await;
}
```

### 5. Testing

**Test on multiple platforms**:
- ✅ Linux (BlueZ)
- ✅ Windows (Windows BLE stack)
- ✅ macOS (CoreBluetooth)
- ✅ Android (Android BLE)
- ✅ iOS (CoreBluetooth)

---

## Resources

### Official Documentation

- [Bluetooth GATT Specifications](https://www.bluetooth.com/specifications/specs/gatt-specification-supplement/)
- [Bluetooth Assigned Numbers](https://www.bluetooth.com/specifications/assigned-numbers/) (Standard UUIDs)
- [TrouBLE Documentation](https://github.com/embassy-rs/trouble)
- [Embassy Framework](https://embassy.dev/)

### Tools

- [nRF Connect](https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-mobile) (Mobile BLE scanner)
- [LightBlue](https://punchthrough.com/lightblue/) (iOS BLE scanner)
- [Wireshark](https://www.wireshark.org/) with BLE sniffer (protocol analysis)
- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)

### HID Resources

- [USB HID Usage Tables](https://usb.org/sites/default/files/hut1_21_0.pdf)
- [HID Report Descriptor Tool](https://eleccelerator.com/usbdescreqparser/)
- [HID-over-GATT Profile](https://www.bluetooth.org/docman/handlers/downloaddoc.ashx?doc_id=245141)

---

## Summary

This guide covered:

✅ **GATT Fundamentals**: Services, characteristics, properties, descriptors
✅ **Current Implementation**: Custom joystick service with X/Y characteristics
✅ **Adding Characteristics**: Button support, battery level, configuration
✅ **HID-over-GATT**: Standard gamepad implementation for universal compatibility
✅ **Testing**: Web Bluetooth, Python, bluetoothctl, mobile apps
✅ **Troubleshooting**: Common issues and solutions

**Next steps**:
1. Try adding button support (Example 1)
2. Implement HID-over-GATT for gamepad mode
3. Test on multiple platforms
4. Optimize for your use case (latency vs battery life)

For implementation help, see:
- [BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md) - Architecture details
- [RUST.md](RUST.md) - Code explanation
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures
