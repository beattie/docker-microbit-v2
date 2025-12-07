# BLE Joystick Implementation

## Overview
This implementation adds Bluetooth Low Energy (BLE) support to the micro:bit v2 joystick project. The joystick data is transmitted wirelessly via BLE to any connected device.

## Features Implemented

### ✅ Custom GATT Service
- **Service UUID**: `12345678-1234-5678-1234-56789abcdef0`
- **Characteristics**:
  - **X-Axis** (`12345678-1234-5678-1234-56789abcdef1`): Read, Notify
  - **Y-Axis** (`12345678-1234-5678-1234-56789abcdef2`): Read, Notify

### ✅ Core Functionality
1. **Advertising**: Device advertises as `"microbit-joy"`
2. **Connection Handling**: Accepts single BLE connection
3. **Real-time Notifications**: Sends joystick data at 10Hz (100ms intervals)
4. **Auto-Reconnect**: Returns to advertising after disconnection

## Architecture

### Task Structure
```
┌─────────────────┐
│   LED Blink     │ - Visual feedback
└─────────────────┘

┌─────────────────┐
│ Joystick Reader │ - Reads ADC at 10Hz
│                 │ - Calibrates center position
│                 │ - Signals data via JOYSTICK_SIGNAL
└─────────────────┘

┌─────────────────┐
│   MPSL Task     │ - Runs BLE protocol stack
└─────────────────┘

┌─────────────────┐
│  BLE Runner     │ - Handles BLE host operations
└─────────────────┘

┌─────────────────┐
│ BLE App Task    │ - Advertising
│                 │ - Connection management
│                 │ - GATT event handling
│                 │ - Sends notifications
└─────────────────┘
```

### Data Flow
```
Joystick Hardware
      ↓
   ADC (SAADC)
      ↓
Calibration & Conversion
      ↓
JOYSTICK_SIGNAL (embassy_sync::Signal)
      ↓
BLE Connection Task
      ↓
GATT Notifications
      ↓
Connected Device
```

## Dependencies

### Key Crates
- `microbit-bsp = "0.4.0"` with `trouble` feature
- `trouble-host = "0.2.0"` with `gatt`, `peripheral`, `defmt` features
- `embassy-executor`, `embassy-time`, `embassy-sync` for async runtime
- `embassy-nrf` for nRF52833 peripheral access

## Testing

### Testing with Mobile Apps

**nRF Connect** (Android/iOS):
1. Scan for BLE devices
2. Connect to `"microbit-joy"`
3. Expand Unknown Service (UUID: `12345678-1234-5678-1234-56789abcdef0`)
4. Enable notifications on X-Axis and Y-Axis characteristics
5. Move joystick - watch values update (0-1023, center at 512)

**LightBlue** (iOS/macOS):
1. Scan and connect to `"microbit-joy"`
2. Find custom service
3. Subscribe to notifications
4. View real-time joystick data

### Expected Values
- **Range**: 0 - 1023 for both axes
- **Center**: ~512 (calibrated at startup)
- **X-Axis**: Inverted (positive = LEFT, negative = RIGHT)
- **Y-Axis**: Inverted (positive = UP, negative = DOWN)

## Building and Flashing

```bash
# Build
cargo build --release

# Flash (using probe-rs)
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Or use Embed.toml with cargo-embed
cargo embed --release
```

## Code Structure

### Key Components

**GATT Server Definition** (`src/main.rs:31-44`):
```rust
#[gatt_server]
struct JoystickServer {
    joystick_service: JoystickService,
}

#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,
}
```

**Data Sharing** (`src/main.rs:22`):
```rust
static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();
```

**Joystick Task**: Reads ADC, calibrates, and signals data
**Connection Task**: Handles GATT events and sends notifications using `select()`

## Known Limitations

1. **Single Connection**: Only supports one BLE connection at a time
2. **No Security**: No pairing/bonding implemented (suitable for demos)
3. **Fixed Address**: Uses hardcoded random static address
4. **No Service Discovery**: Clients must know UUIDs
5. **Update Rate**: Fixed at 10Hz (100ms) - matches joystick sample rate

## Future Enhancements

### Short Term
- [ ] Add connection status LED indicator
- [ ] Implement button press as BLE characteristic
- [ ] Add battery level service
- [ ] Configurable device name via characteristic

### Medium Term
- [ ] HID-over-GATT implementation (appears as gamepad)
- [ ] Security/pairing support
- [ ] Connection parameters negotiation
- [ ] Multiple simultaneous connections

### Long Term
- [ ] Custom mobile app (Flutter/React Native)
- [ ] Web Bluetooth interface
- [ ] Over-the-air (OTA) firmware updates
- [ ] Low-power mode optimization

## Troubleshooting

### Device Not Advertising
- Check MPSL task is running
- Verify BLE initialization succeeded
- Check logs for initialization errors

### Cannot Connect
- Ensure only one device connects at a time
- Reset micro:bit and retry
- Check BLE scanner shows "microbit-joy"

### No Notifications Received
- Verify notifications are enabled (CCCD write)
- Check joystick is moving
- Monitor defmt logs for errors

### Build Errors
- Ensure correct Rust toolchain: `rustup target add thumbv7em-none-eabihf`
- Clean build: `cargo clean && cargo build --release`
- Check dependency versions match Cargo.toml

## Resources

- [TrouBLE Documentation](https://embassy.dev/trouble)
- [micro:bit BSP](https://github.com/lulf/microbit-bsp)
- [Embassy Book](https://embassy.dev/book)
- [nRF52833 Datasheet](https://www.nordicsemi.com/products/nrf52833)
- [Bluetooth GATT Specifications](https://www.bluetooth.com/specifications/specs/gatt-specification-supplement/)

## License

Same as parent project.
