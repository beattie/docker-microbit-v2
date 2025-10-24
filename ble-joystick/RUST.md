# Rust Code Explanation - BLE Joystick for micro:bit v2

This document provides a comprehensive explanation of the Rust implementation in `src/main.rs`, covering embedded systems concepts, async programming with Embassy, and Bluetooth Low Energy (BLE) using the TrouBLE stack.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Embedded Rust Fundamentals](#embedded-rust-fundamentals)
3. [Code Walkthrough](#code-walkthrough)
4. [Data Flow](#data-flow)
5. [Key Rust Concepts](#key-rust-concepts)
6. [Memory Usage](#memory-usage)

---

## Architecture Overview

The application consists of four concurrent async tasks:

```
┌─────────────────┐
│  Main Executor  │
└────────┬────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
    ┌────▼─────┐  ┌──────────┐  ┌───────────┐ │
    │LED Blink │  │Joystick  │  │BLE Stack  │ │
    │Task      │  │ADC Task  │  │(MPSL +    │ │
    │          │  │          │  │ Runner)   │ │
    └──────────┘  └────┬─────┘  └─────┬─────┘ │
                       │              │       │
                       │ SIGNAL       │       │
                       ▼              ▼       │
                  ┌────────────────────────┐  │
                  │  BLE App Task          │◀─┘
                  │  - Advertising         │
                  │  - Connection Handling │
                  │  - GATT Notifications  │
                  └────────────────────────┘
```

**Task Communication:**
- Joystick ADC Task reads analog values and sends them via `JOYSTICK_SIGNAL`
- BLE App Task receives joystick data and sends BLE notifications to connected devices
- All tasks run concurrently using Embassy's cooperative async runtime

---

## Embedded Rust Fundamentals

### The `no_std` Environment (Lines 1-2)

```rust
#![no_std]
#![no_main]
```

**What does this mean?**

- `#![no_std]`: We don't have access to Rust's standard library (std)
  - No heap allocator by default
  - No `Vec`, `String`, `HashMap`, etc.
  - No file system, threading, or OS features
  - Only `core` library (platform-agnostic primitives)

- `#![no_main]`: We don't use the standard `fn main()` entry point
  - Instead, we use `#[embassy_executor::main]` macro
  - This sets up the async executor and handles low-level initialization

**Why?**
The micro:bit v2 is a bare-metal embedded system with:
- **512KB flash** (program storage)
- **128KB RAM** (working memory)
- **No operating system** - we run directly on the hardware
- **Nordic nRF52833** ARM Cortex-M4 processor

### Imports (Lines 4-12)

```rust
use defmt::{info, warn, error, Debug2Format};
```
- `defmt`: Efficient logging for embedded systems (logs via debug probe, not serial)
- Format strings compiled out, only indexes sent over wire

```rust
use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use embassy_sync::signal::Signal;
use embassy_sync::blocking_mutex::raw::ThreadModeRawMutex;
use embassy_futures::select::select;
```
- **Embassy**: Async/await framework for embedded Rust
- `Spawner`: Creates new async tasks
- `Timer`: Non-blocking delays
- `Signal`: Single-value communication between tasks (like a 1-element channel)
- `select`: Wait for the first of multiple futures to complete

```rust
use microbit_bsp::{ble::MultiprotocolServiceLayer, display, Config, Microbit};
```
- **Board Support Package (BSP)**: Hardware abstraction for micro:bit v2
- Pre-configured peripherals (LED matrix, BLE, ADC, etc.)

```rust
use trouble_host::prelude::*;
```
- **TrouBLE**: BLE Host stack implementation in Rust
- Provides GATT server, advertising, connection management

```rust
use {defmt_rtt as _, panic_probe as _};
```
- **defmt_rtt**: Real-Time Transfer (RTT) logging via debug probe
- **panic_probe**: On panic, print backtrace and halt (helps debugging)

---

## Code Walkthrough

### Data Structures (Lines 14-22)

```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,  // 0-1023 range, center at 512
    y: u16,  // 0-1023 range, center at 512
}
```

**Key Points:**
- `Clone, Copy`: Can be duplicated with simple memory copy (no heap allocation)
- `Debug, defmt::Format`: Can be printed with `{:?}` in logs
- `u16`: Unsigned 16-bit integer (0-65535), but we only use 0-1023
- Values are **10-bit ADC resolution** mapped to center at 512

```rust
static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();
```

**What is this?**
- **`static`**: Global variable with `'static` lifetime (exists for entire program)
- **`Signal`**: A synchronization primitive for sharing a single value between tasks
  - Producer calls `.signal(value)` to update
  - Consumer calls `.wait()` to get latest value (blocks if no new value)
- **`ThreadModeRawMutex`**: Mutex type for single-core systems (no interrupts during access)

**Why Signal instead of Channel?**
- Signal always holds the **latest value** (overwrites old values)
- Perfect for joystick: we only care about current position, not history
- Channel would queue values, wasting memory

### BLE Constants (Lines 24-28)

```rust
const CONNECTIONS_MAX: usize = 1;
const L2CAP_CHANNELS_MAX: usize = 2; // Signal + att
```

**Memory allocation for BLE stack:**
- We only support 1 simultaneous connection
- L2CAP channels: 2 (signaling channel + ATT protocol for GATT)
- These constants are used to allocate static buffers at compile time

### GATT Server Definition (Lines 30-44)

```rust
#[gatt_server]
struct JoystickServer {
    joystick_service: JoystickService,
}
```

**Procedural Macro Magic:**
The `#[gatt_server]` macro **generates code** at compile time:
- Creates methods like `new_with_config()`
- Implements BLE service registration
- Handles characteristic read/write/notify operations

```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,
}
```

**GATT Service Structure:**
- **Service UUID**: Custom UUID identifying our joystick service
- **Characteristics**: Two u16 values (X and Y axis)
  - `read`: Client can read current value
  - `notify`: Server can push updates to client (no polling needed)

**Generated Code:**
The macro creates methods like:
```rust
impl JoystickService {
    fn x_axis(&self) -> CharacteristicHandle<u16> { ... }
    fn y_axis(&self) -> CharacteristicHandle<u16> { ... }
}
```

### LED Blink Task (Lines 46-76)

```rust
#[embassy_executor::task]
async fn led_blink_task(mut display: display::LedMatrix<embassy_nrf::gpio::Output<'static>, 5, 5>) {
```

**Task Definition:**
- `#[embassy_executor::task]`: Marks this as an async task (cooperative multitasking)
- `async fn`: Function that can `await` without blocking other tasks
- Ownership: Takes `display` by value (moves ownership into task)

**Lifetime `'static`:**
```rust
Output<'static>
```
- Means GPIO pins live for the entire program (never dropped)
- Required because tasks run indefinitely

**LED Pattern Creation:**
```rust
let all_off = display::Frame::empty();

let mut top_row = display::Frame::empty();
top_row.set(0, 0);
top_row.set(0, 1);
// ... sets all LEDs in row 0
```

**Frame**: 5x5 bitmap for LED matrix
- `set(row, col)`: Turn on LED at position
- `empty()`: All LEDs off

**Startup Sequence:**
```rust
for i in 1..=3 {
    info!("Startup blink {}/3", i);
    display.display(top_row, Duration::from_millis(150)).await;
    display.display(all_off, Duration::from_millis(150)).await;
}
```

**`await` keyword:**
- `.await` yields control to executor while waiting
- Other tasks can run during the 150ms delay
- No busy-waiting, no CPU cycles wasted

**Main Loop:**
```rust
loop {
    display.display(top_row, Duration::from_millis(500)).await;
    display.display(all_off, Duration::from_millis(500)).await;
}
```
- Blinks top row every 1 second (500ms on, 500ms off)
- Runs forever (never returns)

### Joystick ADC Task (Lines 78-207)

```rust
#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
) {
```

**Peripheral Ownership:**
- `Peri<'static, T>`: Wrapper ensuring exclusive access to hardware peripheral
- `SAADC`: Successive Approximation ADC (analog-to-digital converter)
- `P0_03`, `P0_04`: GPIO pins (P1 and P2 on micro:bit edge connector)

**Why move peripherals into tasks?**
- Rust's ownership system prevents multiple tasks from accessing same hardware
- Compile-time safety: no data races on hardware registers

**Interrupt Binding:**
```rust
bind_interrupts!(struct Irqs {
    SAADC => embassy_nrf::saadc::InterruptHandler;
});
```
- Macro connects hardware interrupt to Embassy's async driver
- When ADC finishes conversion, interrupt wakes the task

**ADC Configuration:**
```rust
let mut config = Config::default();
config.resolution = Resolution::_12BIT;
config.oversample = Oversample::OVER4X;
```
- **12-bit resolution**: 0-4095 range (we use 0-1023, 10-bit effective)
- **4x oversampling**: Takes 4 samples and averages (reduces noise)

**Channel Configuration:**
```rust
let mut adc = Saadc::new(
    saadc,
    Irqs,
    config,
    [
        ChannelConfig::single_ended(p1),
        ChannelConfig::single_ended(p2),
    ],
);
```
- Two channels: P1 (X-axis) and P2 (Y-axis)
- Single-ended: Measures voltage relative to ground (0-3.3V)

**Calibration (Lines 114-129):**
```rust
let mut cal_buf = [0i16; 2];
let mut x_cal_sum = 0i32;
let mut y_cal_sum = 0i32;

for _ in 0..10 {
    adc.sample(&mut cal_buf).await;
    x_cal_sum += cal_buf[0] as i32;
    y_cal_sum += cal_buf[1] as i32;
    Timer::after(Duration::from_millis(10)).await;
}

let x_center = (x_cal_sum / 10) as i16;
let y_center = (y_cal_sum / 10) as i16;
```

**Why calibrate?**
- Joystick center position varies slightly between units
- Manufacturing tolerances mean "center" might be 2045 instead of 2048
- We measure center on startup, then calculate deviations from that

**Main Reading Loop (Lines 135-206):**
```rust
loop {
    adc.sample(&mut buf).await;

    let x_raw = buf[0];
    let y_raw = buf[1];

    let x_delta = x_raw - x_center;
    let y_delta = y_raw - y_center;

    // Convert to 0-1023 range with center at 512
    let x_value = (512 + (x_delta as i32 * 512 / 2000).clamp(-512, 511)) as u16;
    let y_value = (512 + (y_delta as i32 * 512 / 2000).clamp(-512, 511)) as u16;
```

**Conversion Math:**
1. Read raw ADC value (e.g., 2045)
2. Calculate deviation from center (e.g., 2045 - 2048 = -3)
3. Scale to 0-1023 range:
   - Assume full range is ±2000 from center
   - `delta * 512 / 2000` scales delta to ±512
   - Add 512 to shift to 0-1024 range
   - `clamp(-512, 511)` prevents overflow
4. Cast to u16

**Signal Sending:**
```rust
let joystick_data = JoystickData {
    x: x_value,
    y: y_value,
};
JOYSTICK_SIGNAL.signal(joystick_data);
```
- Updates global signal with latest joystick position
- Any waiting task will be woken up

**Movement Detection (Lines 179-201):**
```rust
let threshold = 150;
let deadzone = 50;

if x_centered.abs() > deadzone || y_centered.abs() > deadzone {
    if x_centered.abs() > threshold || y_centered.abs() > threshold {
        if x_centered.abs() > y_centered.abs() {
            if x_centered > 0 {
                info!("  → Movement: LEFT");
            } else {
                info!("  → Movement: RIGHT");
            }
        } else {
            if y_centered > 0 {
                info!("  → Movement: UP");
            } else {
                info!("  → Movement: DOWN");
            }
        }
    }
}
```

**Deadzone Logic:**
- Deadzone (50): Ignore tiny movements near center (noise)
- Threshold (150): Only log significant movements
- Axes are inverted in hardware:
  - X: positive = LEFT, negative = RIGHT
  - Y: positive = UP, negative = DOWN

**Sample Rate:**
```rust
Timer::after(Duration::from_millis(100)).await;
```
- 10 Hz (100ms between samples)
- Balance between responsiveness and CPU usage

### BLE Tasks (Lines 209-324)

#### MPSL Task (Lines 210-213)

```rust
#[embassy_executor::task]
async fn mpsl_task(mpsl: &'static MultiprotocolServiceLayer<'static>) -> ! {
    mpsl.run().await
}
```

**What is MPSL?**
- **Multiprotocol Service Layer**: Nordic's proprietary radio driver
- Handles low-level RF timing and protocols
- Shared between BLE, 802.15.4, and proprietary protocols

**Return type `-> !`:**
- "Never type" - function never returns
- Runs forever in infinite loop

**Reference `&'static`:**
- Task borrows MPSL instead of owning it
- `'static`: Reference valid for entire program lifetime

#### BLE Runner Task (Lines 215-220)

```rust
async fn ble_runner_task<C: Controller, P: PacketPool>(
    mut runner: Runner<'_, C, P>,
) -> Result<(), BleHostError<C::Error>> {
    runner.run().await
}
```

**Generic Parameters:**
- `C: Controller`: BLE controller implementation (Nordic SoftDevice in our case)
- `P: PacketPool`: Memory pool for BLE packets

**What does it do?**
- Processes BLE stack events (connections, L2CAP, security, etc.)
- Must run concurrently with application code
- Communicates with `ble_app_task` via internal channels

#### Advertising Function (Lines 222-251)

```rust
async fn advertise<'a, 'b, C: Controller>(
    name: &'a str,
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, BleHostError<C::Error>> {
```

**Lifetime Annotations:**
- `'a`: Lifetime of advertisement data (must outlive function)
- `'b`: Lifetime of GATT server (must outlive connection)
- Ensures data isn't dropped while BLE stack is using it

**Advertisement Data:**
```rust
let mut advertiser_data = [0; 31];
AdStructure::encode_slice(
    &[
        AdStructure::Flags(LE_GENERAL_DISCOVERABLE | BR_EDR_NOT_SUPPORTED),
        AdStructure::CompleteLocalName(name.as_bytes()),
    ],
    &mut advertiser_data[..],
)?;
```

**BLE Advertisement Packet:**
- Max 31 bytes for advertisement data
- Flags: "I'm discoverable BLE-only device"
- Local Name: "microbit-joy" (shows up in BLE scanner)

**Starting Advertiser:**
```rust
let advertiser = peripheral
    .advertise(
        &Default::default(),
        Advertisement::ConnectableScannableUndirected {
            adv_data: &advertiser_data[..],
            scan_data: &[],
        },
    )
    .await?;
```

**ConnectableScannableUndirected:**
- Anyone can connect (no whitelist)
- Can be scanned for more info
- Undirected (not targeted at specific device)

**Accepting Connection:**
```rust
let conn = advertiser.accept().await?.with_attribute_server(server)?;
```
- `.accept()` blocks until device connects
- `.with_attribute_server()` attaches our GATT server
- Returns `GattConnection` for handling requests/notifications

#### Connection Task (Lines 253-296)

```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;

    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
```

**Characteristic Handles:**
- `x_char`, `y_char`: Handles for updating characteristic values
- Initialize to 512 (center position)

**Event Loop with `select`:**
```rust
loop {
    let gatt_event_future = conn.next();
    let joystick_update_future = JOYSTICK_SIGNAL.wait();

    match select(gatt_event_future, joystick_update_future).await {
```

**Why `select`?**
- Waits for **whichever happens first**:
  1. GATT event (read request, disconnect, etc.)
  2. New joystick data from signal

**Handling GATT Events:**
```rust
embassy_futures::select::Either::First(event) => {
    match event {
        GattConnectionEvent::Disconnected { reason } => {
            info!("[BLE] Disconnected: {:?}", reason);
            break;
        }
        GattConnectionEvent::Gatt { event } => {
            match event.accept() {
                Ok(reply) => reply.send().await,
                Err(e) => warn!("[BLE] Error sending response: {:?}", e),
            }
        }
        _ => {}
    }
}
```

**Event Handling:**
- `Disconnected`: Exit loop, return to advertising
- `Gatt`: Client read request, send current value
- `accept()`: Process request, generate response
- `send()`: Send response to client

**Handling Joystick Updates:**
```rust
embassy_futures::select::Either::Second(data) => {
    // Update characteristic values and notify
    let _ = x_char.set(server, &data.x);
    let _ = y_char.set(server, &data.y);
    let _ = x_char.notify(conn, &data.x).await;
    let _ = y_char.notify(conn, &data.y).await;
}
```

**Notification Flow:**
1. Set new value in GATT server
2. Send notification to connected client
3. Client receives update without polling

**Why ignore errors (`let _ = ...`)?**
- Client might not have enabled notifications
- Connection might drop mid-notification
- We continue regardless (best-effort delivery)

#### BLE Application Task (Lines 298-324)

```rust
async fn ble_app_task<C: Controller>(
    mut peripheral: Peripheral<'_, C, DefaultPacketPool>,
) {
    let server = JoystickServer::new_with_config(GapConfig::Peripheral(PeripheralConfig {
        name: "microbit-joy",
        appearance: &appearance::power_device::GENERIC_POWER_DEVICE,
    }))
    .expect("Failed to create GATT server");
```

**GAP Configuration:**
- **GAP**: Generic Access Profile (BLE device info)
- `name`: Device name for connection (different from advertised name)
- `appearance`: Standard BLE appearance value (shows icon in some apps)

**Main Loop:**
```rust
loop {
    match advertise("microbit-joy", &mut peripheral, &server).await {
        Ok(conn) => {
            connection_task(&server, &conn).await;
        }
        Err(e) => {
            let e = Debug2Format(&e);
            warn!("[BLE] Advertising error: {:?}", e);
            Timer::after(Duration::from_secs(1)).await;
        }
    }
}
```

**State Machine:**
1. Start advertising
2. Wait for connection
3. Handle connection (until disconnect)
4. Go back to step 1

**Error Handling:**
- If advertising fails, wait 1 second and retry
- Prevents rapid retry loop on persistent errors

### Main Function (Lines 326-381)

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
```

**`#[embassy_executor::main]` macro:**
- Replaces standard `fn main()`
- Sets up Embassy executor (async runtime)
- Initializes interrupt handlers
- Calls our async main function

**Spawner:**
- Used to create new concurrent tasks
- Each task runs independently

**Board Initialization:**
```rust
let board = Microbit::new(Config::default());
```
- Creates `Microbit` struct with all peripherals
- Consumes peripherals (can't access twice)
- Returns struct with GPIO, ADC, BLE, timers, etc.

**Spawning Tasks:**
```rust
match spawner.spawn(led_blink_task(board.display)) {
    Ok(_) => info!("✓ LED task spawned"),
    Err(_) => error!("✗ Failed to spawn LED task"),
}
```

**Task Spawning:**
- Moves `board.display` into task (ownership transfer)
- Task runs concurrently with main
- If spawn fails, arena is full (increase `task-arena-size` in Cargo.toml)

**BLE Initialization:**
```rust
let (sdc, mpsl) = board
    .ble
    .init(board.timer0, board.rng)
    .expect("BLE Stack failed to initialize");
```

**Nordic SoftDevice Controller (SDC):**
- `board.timer0`: High-precision timer for BLE timing
- `board.rng`: Random number generator for addresses/encryption
- Returns controller + MPSL instances

**must_spawn:**
```rust
spawner.must_spawn(mpsl_task(mpsl));
```
- Like `spawn`, but panics on failure
- MPSL task is critical for BLE operation

**BLE Address:**
```rust
let address = Address::random([0x41, 0x5A, 0xE3, 0x1E, 0x10, 0xC9]);
```
- Random static address (doesn't change between reboots)
- Format: `C9:10:1E:E3:5A:41`

**Host Resources:**
```rust
let mut resources: HostResources<DefaultPacketPool, CONNECTIONS_MAX, L2CAP_CHANNELS_MAX> =
    HostResources::new();
let stack = trouble_host::new(sdc, &mut resources).set_random_address(address);
```

**Static Memory Allocation:**
- Allocates buffers for connections and L2CAP channels
- Fixed size at compile time (no dynamic allocation)
- Uses const generics for type safety

**Building BLE Stack:**
```rust
let Host {
    peripheral,
    runner,
    ..
} = stack.build();
```

**Returns:**
- `peripheral`: For advertising and accepting connections
- `runner`: Processes BLE stack events
- Other parts ignored (`..`)

**Running Forever:**
```rust
select(ble_runner_task(runner), ble_app_task(peripheral)).await;
```

**Why `select`?**
- Both tasks run concurrently until one completes
- If either task panics or returns, program stops
- In practice, both run forever

---

## Data Flow

### Complete Flow Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                         HARDWARE                               │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ Analog Voltage (0-3.3V)
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                    SAADC Peripheral                            │
│  • 12-bit ADC with 4x oversampling                            │
│  • Channels: P0_03 (X), P0_04 (Y)                             │
│  • Interrupt-driven sampling                                   │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ i16 values (-2048 to 2047)
                              ▼
┌───────────────────────────────────────────────────────────────┐
│              joystick_read_task()                              │
│  1. Sample ADC channels                                        │
│  2. Calculate delta from calibrated center                     │
│  3. Scale to 0-1023 range (center = 512)                      │
│  4. Create JoystickData { x, y }                              │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ JOYSTICK_SIGNAL.signal(data)
                              ▼
┌───────────────────────────────────────────────────────────────┐
│        static JOYSTICK_SIGNAL: Signal<...>                     │
│  • Thread-safe single-value storage                           │
│  • Wakes waiting tasks on update                              │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ JOYSTICK_SIGNAL.wait()
                              ▼
┌───────────────────────────────────────────────────────────────┐
│              connection_task()                                 │
│  • select() on:                                               │
│    - GATT events (read, disconnect)                           │
│    - Joystick updates                                         │
│  • On update:                                                 │
│    - x_char.set(server, &data.x)                             │
│    - x_char.notify(conn, &data.x)                            │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ BLE Notifications
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  BLE Radio (nRF52833)                          │
│  • GATT notifications sent wirelessly                         │
│  • Characteristic UUIDs: ...def1 (X), ...def2 (Y)            │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ 2.4 GHz radio waves
                              ▼
┌───────────────────────────────────────────────────────────────┐
│            Connected BLE Client (Phone/PC)                     │
│  • Receives notifications at ~10 Hz                           │
│  • Displays X/Y values: 0-1023                                │
└───────────────────────────────────────────────────────────────┘
```

### Timing Diagram

```
Time →
─────────────────────────────────────────────────────────────►

joystick_read_task:
  │◄─100ms─►│◄─100ms─►│◄─100ms─►│◄─100ms─►│
  Sample      Sample    Sample    Sample
    ↓           ↓         ↓         ↓
  Signal      Signal    Signal    Signal
    ↓           ↓         ↓         ↓

connection_task:
  │           │         │         │
  wait()      wait()    wait()    wait()
    ↓           ↓         ↓         ↓
  notify()    notify()  notify()  notify()
    ↓           ↓         ↓         ↓

BLE Radio:
  │           │         │         │
  TX packet   TX packet TX packet TX packet
  ───►        ───►      ───►      ───►

Client:
  │           │         │         │
  RX          RX        RX        RX
  (10-50ms    (10-50ms  (10-50ms  (10-50ms
   latency)   latency)  latency)  latency)
```

---

## Key Rust Concepts

### 1. Ownership and Move Semantics

**Example from `main()`:**
```rust
spawner.spawn(led_blink_task(board.display))
```

- `board.display` is **moved** into the task
- After this line, `board.display` can't be used in `main()`
- Prevents multiple tasks from accessing the same peripheral

**Why is this safe?**
- Compiler enforces: only one owner of `display` at a time
- No locks, no runtime checks needed
- **Zero-cost abstraction**: No performance overhead

### 2. Lifetimes

**Example from `advertise()`:**
```rust
async fn advertise<'a, 'b, C: Controller>(
    name: &'a str,
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, ...>
```

**What are lifetimes?**
- `'a`, `'b`: Named lifetimes (like variables for scopes)
- Ensures references don't outlive the data they point to
- Prevents dangling pointers **at compile time**

**Lifetime relationships:**
- `name: &'a str`: Name string must live at least as long as `'a`
- `peripheral: &mut Peripheral<'a, ...>`: Peripheral uses data with lifetime `'a`
- Return type: `GattConnection<'a, 'b, ...>`: Connection references data from both `'a` and `'b`

**Why explicit lifetimes?**
```rust
let name = String::from("microbit-joy");
let conn = advertise(&name, ...).await?;
drop(name);  // Compiler error! 'name' is still referenced by 'conn'
```

### 3. Async/Await and Cooperative Multitasking

**Traditional threading:**
```
Task A: ────────X─────────X─────────X────────►
Task B: ─X─────────X─────────X─────────X──────►
         │         │         │         │
       Preemption (OS context switch)
```

**Embassy cooperative multitasking:**
```
Task A: ────────.await────────.await──────►
Task B: ──.await────────.await────────.await──►
          │            │            │
        Yield points (cooperative)
```

**Key Differences:**
- **No OS scheduler**: Embassy runtime decides what runs
- **Explicit yield points**: Only yields on `.await`
- **No stack per task**: State machine instead (saves RAM)
- **No preemption**: Task runs until it `.await`s

**How does `.await` work?**

```rust
Timer::after(Duration::from_millis(100)).await;
```

Compiler transforms to state machine:
```rust
enum State {
    Start,
    WaitingForTimer(TimerFuture),
    Done,
}

// Pseudo-code (simplified)
match state {
    Start => {
        state = WaitingForTimer(Timer::after(...));
    }
    WaitingForTimer(timer) => {
        if timer.poll() == Ready {
            state = Done;
        } else {
            return Pending; // Yield to executor
        }
    }
}
```

**Memory efficiency:**
- Task state stored in single enum
- No 8KB+ stack per task (typical OS thread)
- Can run 10+ tasks on 128KB RAM

### 4. Type-State Pattern with Peripherals

**Example:**
```rust
let board = Microbit::new(Config::default());
// board.display is type: LedMatrix<Output<'static>, 5, 5>

spawner.spawn(led_blink_task(board.display));
// board.display moved, can't use again

// Compiler error:
// board.display.clear(); // ❌ value borrowed after move
```

**Type system enforces:**
- Can't use peripheral after moving to task
- Can't initialize peripheral twice
- Can't access from multiple tasks simultaneously

### 5. Zero-Cost Abstractions

**Example: Signal vs manual synchronization**

Without Signal (manual):
```rust
static mut DATA: Option<JoystickData> = None;
static mut DATA_READY: bool = false;

// Producer
unsafe {
    DATA = Some(joystick_data);
    DATA_READY = true;
}

// Consumer
unsafe {
    if DATA_READY {
        let data = DATA.unwrap();
        DATA_READY = false;
        // use data
    }
}
```

With Signal (safe):
```rust
JOYSTICK_SIGNAL.signal(joystick_data);

let data = JOYSTICK_SIGNAL.wait().await;
```

**Performance:**
- Signal compiles to **same machine code** as manual version
- Type system adds safety with **zero runtime cost**
- "Zero-cost abstraction": abstraction has no overhead

### 6. Const Generics

**Example:**
```rust
const CONNECTIONS_MAX: usize = 1;
const L2CAP_CHANNELS_MAX: usize = 2;

let mut resources: HostResources<DefaultPacketPool, CONNECTIONS_MAX, L2CAP_CHANNELS_MAX> =
    HostResources::new();
```

**What does this do?**
- Allocates arrays of exact size at compile time:
```rust
struct HostResources<P, const CONNS: usize, const CHANS: usize> {
    connections: [Connection; CONNS],
    l2cap_channels: [L2capChannel; CHANS],
    // ...
}
```

**Benefits:**
- No heap allocation (no malloc/free)
- Size known at compile time (better optimization)
- Type-safe (can't pass wrong-sized array)

### 7. Procedural Macros

**Example:**
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "...def1", read, notify)]
    x_axis: u16,
    // ...
}
```

**What the macro generates (simplified):**
```rust
impl JoystickService {
    const SERVICE_UUID: Uuid = Uuid::from_bytes([0x12, 0x34, ...]);

    fn new() -> Self { ... }

    fn x_axis(&self) -> CharacteristicHandle<u16> {
        CharacteristicHandle {
            uuid: Uuid::from_bytes([..., 0xf1]),
            properties: READ | NOTIFY,
            // ...
        }
    }
}
```

**Why use macros?**
- Reduces boilerplate (10 lines → 100+ lines of generated code)
- Type-safe UUID handling
- Compile-time validation (wrong UUID format = compile error)

---

## Memory Usage

### Flash (Program Storage): 143 KB / 512 KB (28%)

**Breakdown (approximate):**
- Embassy runtime: ~20 KB
- TrouBLE BLE stack: ~80 KB
- Nordic SoftDevice Controller: ~30 KB
- Application code: ~10 KB
- defmt logging: ~3 KB

**Optimization level:**
```toml
[profile.release]
opt-level = "z"  # Optimize for size
```

- `opt-level = 3`: Speed optimized, ~180 KB
- `opt-level = "z"`: Size optimized, ~143 KB
- Trade-off: Slightly slower, but fits comfortably

### RAM (Working Memory): 44 KB / 128 KB (34%)

**Breakdown (approximate):**
- BLE stack buffers: ~20 KB
  - Packet pools (TX/RX)
  - L2CAP channels
  - Connection state
- Embassy executor: ~8 KB
  - Task arenas
  - Signal storage
- Static buffers: ~4 KB
  - Advertisement data
  - GATT server tables
- Task state machines: ~6 KB
  - LED task state
  - Joystick task state
  - BLE task states
- Stack: ~6 KB
  - Main stack
  - Interrupt stack

**Why so little?**
- No heap (no malloc)
- No OS (no kernel structures)
- State machines instead of task stacks
- Static allocation (known at compile time)

### Comparison to C/Arduino

**Arduino BLE (C++):**
- Typically uses 60-80 KB RAM
- Dynamic allocation (heap fragmentation)
- Larger code size (~200+ KB)

**Rust embedded:**
- More memory efficient (44 KB RAM)
- No heap fragmentation
- Smaller code (143 KB)
- **Same or better performance**

**Safety:**
- C: Undefined behavior possible (buffer overflows, use-after-free)
- Rust: Compile-time safety guarantees (no UB in safe code)

---

## Advanced Topics

### 1. Interrupt Handling

**How interrupts work with Embassy:**

```rust
bind_interrupts!(struct Irqs {
    SAADC => embassy_nrf::saadc::InterruptHandler;
});
```

**Flow:**
1. ADC finishes conversion
2. Hardware triggers SAADC interrupt
3. `InterruptHandler` runs in interrupt context
4. Signals waker for ADC task
5. Executor polls ADC task
6. Task resumes at `.await` point

**Critical: No user code in interrupt!**
- Embassy interrupt handlers are minimal (wake task)
- Actual processing happens in async task
- Prevents long interrupt latency

### 2. BLE Connection Parameters

**Connection Interval:**
- Default: ~30ms (33.75ms to 50ms)
- Can be negotiated with client
- Affects latency and power consumption

**Notification timing:**
- Joystick samples at 10 Hz (100ms)
- BLE connection interval: ~30ms
- Notifications sent within 1-2 connection intervals
- Total latency: ~50-100ms typical

### 3. Power Management

**Current consumption (approximate):**
- Active BLE advertising: ~5 mA
- Connected and idle: ~3 mA
- Connected with notifications: ~4 mA
- LED on: +5 mA per LED

**Embassy power features:**
```rust
Timer::after(Duration::from_millis(100)).await;
```
- During `.await`, CPU enters sleep mode (WFI instruction)
- Radio wakes CPU for BLE events
- Timer wakes CPU after delay
- Automatic power management (no manual sleep calls)

### 4. Error Handling

**Rust's Result type:**
```rust
fn advertise(...) -> Result<GattConnection, BleHostError> {
    // ...
}
```

**Handling:**
```rust
match advertise(...).await {
    Ok(conn) => { /* success */ },
    Err(e) => { /* handle error */ },
}
```

**Unwrapping (panics on error):**
```rust
board.ble.init(...).expect("BLE Stack failed to initialize");
```

**When to panic:**
- Initialization failures (can't continue)
- Resource allocation failures

**When to handle:**
- Connection errors (can retry)
- Notification failures (can ignore)

### 5. Embassy vs FreeRTOS

| Feature | Embassy | FreeRTOS |
|---------|---------|----------|
| Language | Rust | C |
| Task model | Async/await | Preemptive threads |
| Memory per task | ~100 bytes | ~8 KB (stack) |
| Task switching | Cooperative | Preemptive |
| Safety | Compile-time | Runtime |
| RAM usage | Lower | Higher |
| Learning curve | Steeper (Rust) | Gentler (C) |

**When to use Embassy:**
- Memory-constrained systems
- Want safety guarantees
- Comfortable with Rust

**When to use FreeRTOS:**
- Legacy C codebase
- Hard real-time requirements
- Team familiar with C/RTOS

---

## Conclusion

This BLE joystick implementation demonstrates:

1. **Embedded Rust**: Safe systems programming without garbage collection
2. **Async/await**: Efficient cooperative multitasking on bare metal
3. **Type safety**: Compile-time guarantees preventing entire classes of bugs
4. **Zero-cost abstractions**: High-level code with low-level performance
5. **Memory efficiency**: Full BLE stack in 44 KB RAM

**Key takeaways:**
- Rust's ownership system prevents data races at compile time
- Embassy's async runtime enables concurrent tasks without OS overhead
- Type-state patterns enforce correct peripheral usage
- Procedural macros reduce boilerplate while maintaining safety

**Further reading:**
- [Embassy Documentation](https://embassy.dev/)
- [TrouBLE GitHub](https://github.com/embassy-rs/trouble)
- [Embedded Rust Book](https://rust-embedded.github.io/book/)
- [Rust Async Book](https://rust-lang.github.io/async-book/)

---

**Questions?** See [BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md) for architecture details or [TESTING_GUIDE.md](TESTING_GUIDE.md) for hands-on testing.
