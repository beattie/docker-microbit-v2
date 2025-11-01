# BLE Joystick - micro:bit v2

A Bluetooth Low Energy (BLE) joystick implementation for the micro:bit v2, sending real-time analog joystick data wirelessly. Built with Rust using the Embassy async framework and TrouBLE BLE stack.

## 🎮 Features

- **Real-time BLE Notifications**: Joystick X/Y + Button A/B transmitted at 10Hz
- **6 Input Channels**: 2 analog axes + 2 buttons (expandable to 6 buttons)
- **Custom GATT Service**: Standard BLE service with read and notify characteristics
- **Auto-calibration**: Centers joystick position on startup
- **Concurrent Tasks**: LED indicators, joystick reading, and BLE operations run simultaneously
- **Low Memory**: ~140KB flash, ~43KB RAM
- **Production Ready**: Based on official microbit-bsp examples

## 🚀 Quick Start

```bash
# Flash to your micro:bit v2
cargo run --release
```

See [QUICKSTART.md](QUICKSTART.md) for complete 3-minute setup guide.

## 📱 Testing

**Python GUI (⭐ Recommended - works on all platforms):**
```bash
pip install bleak
python3 test/gui_test.py
```

**Web Bluetooth (Chrome/Chromium/Edge only - Firefox NOT supported):**
```bash
cd test/
./serve.sh
# Then open in Chrome: http://localhost:8000/ble-test.html
```

**Python Console Script:**
```bash
pip install bleak
python3 test/test_buttons.py
```

**On your smartphone:**
1. Install nRF Connect (Android/iOS) or LightBlue (iOS)
2. Scan for "microbit-joy"
3. Connect and enable notifications
4. Move joystick and press buttons → Watch values update!

See [BUTTON_TEST.md](BUTTON_TEST.md) for complete testing guide.

## 🛠️ Hardware

- **[micro:bit v2](https://en.wikipedia.org/wiki/Micro_Bit)** - Nordic nRF52833 (Cortex-M4)
- **[joystick:bit](https://wiki.elecfreaks.com/en/microbit/expansion-board/joystick-bit-v2/)** - Analog joystick on P1 (X-axis) and P2 (Y-axis)
- **USB cable** for programming

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 3-minute flash and test guide
- **[BUTTON_TEST.md](BUTTON_TEST.md)** - Button + joystick testing guide
- **[JOYSTICK_BIT_EXERCISE.md](JOYSTICK_BIT_EXERCISE.md)** - Add 4 more buttons, buzzer, vibration motor
- **[GATT.md](GATT.md)** - Complete GATT implementation guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing with multiple BLE apps
- **[BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md)** - Architecture and implementation details
- **[LINUX_TESTING.md](LINUX_TESTING.md)** - Testing from a Linux system

## 🔧 Building

**Prerequisites:**
```bash
# Install Rust target
rustup target add thumbv7em-none-eabihf

# Install probe-rs (flashing tool)
cargo install probe-rs-tools
```

**Build:**
```bash
cargo build --release
```

**Flash:**
```bash
cargo run --release
```

## 📊 System Architecture

```
Hardware Layer          Application Layer         BLE Layer
┌─────────────┐        ┌──────────────┐        ┌─────────────┐
│ Joystick:bit│───────▶│ ADC Sampling │───────▶│ GATT Server │
│  P1 (X-Axis)│        │  Calibration │        │  X-Axis Char│
│  P2 (Y-Axis)│        │  10Hz Rate   │        │  Y-Axis Char│
└─────────────┘        └──────────────┘        └─────────────┘
                              │                        │
                              ▼                        ▼
┌─────────────┐        ┌──────────────┐        ┌─────────────┐
│ LED Matrix  │◀───────│ Signal Coord │        │ Advertising │
│   5x5 LEDs  │        │  (embassy_   │        │  "microbit- │
└─────────────┘        │   sync)      │        │   joy"      │
                       └──────────────┘        └─────────────┘
```

## 🔌 BLE Service Specification

**Service UUID**: `12345678-1234-5678-1234-56789abcdef0`

**Characteristics:**
| Characteristic | UUID | Properties | Type | Range/Values |
|---------------|------|------------|------|--------------|
| X-Axis | `...def1` | Read, Notify | u16 | 0-1023 |
| Y-Axis | `...def2` | Read, Notify | u16 | 0-1023 |
| Button A | `...def3` | Read, Notify | u8 | 0=released, 1=pressed |
| Button B | `...def4` | Read, Notify | u8 | 0=released, 1=pressed |

**Center Position**: X=512, Y=512 (calibrated at startup)

**Expansion Ready**: See [JOYSTICK_BIT_EXERCISE.md](JOYSTICK_BIT_EXERCISE.md) to add buttons C, D, E, F + buzzer + vibration

## 🧩 Dependencies

- `microbit-bsp = "0.4.0"` - Board support package with BLE
- `trouble-host = "0.2.0"` - BLE stack (TrouBLE)
- `embassy-executor`, `embassy-time`, `embassy-sync` - Async runtime
- `embassy-nrf = "0.4.1"` - nRF52833 HAL

See [Cargo.toml](Cargo.toml) for complete dependency list.

## 📈 Performance

- **Flash Usage**: 140KB / 512KB (27%)
- **RAM Usage**: 43KB / 128KB (34%)
- **Update Rate**: 10Hz (100ms interval)
- **BLE Latency**: ~30-50ms typical
- **Button Latency**: ~10ms to RTT, ~30-50ms to BLE

## 🎯 Project Status

✅ **Implemented:**
- [x] Analog joystick reading with ADC
- [x] Automatic center calibration
- [x] BLE advertising and connection handling
- [x] Custom GATT service with notifications
- [x] Real-time data streaming (joystick + buttons)
- [x] Button A/B press detection
- [x] LED visual feedback
- [x] Web Bluetooth test interface
- [x] Python test script
- [x] Comprehensive documentation

🚧 **Ready to Add:** (See [JOYSTICK_BIT_EXERCISE.md](JOYSTICK_BIT_EXERCISE.md))
- [ ] 4 additional buttons (C, D, E, F on P12-P15)
- [ ] Buzzer support (P0 with PWM)
- [ ] Vibration motor (P16 for haptic feedback)
- [ ] HID-over-GATT (standard gamepad support)
- [ ] Battery level reporting
- [ ] Configurable sensitivity

## 🤝 Contributing

This project was created as a learning experience using generative AI (Claude) to demonstrate BLE on embedded Rust. Feel free to use it as a reference for your own projects!

## 📝 License

MIT or Apache-2.0 (your choice)

## 🙏 Acknowledgments

- Built with [Embassy](https://embassy.dev/) async runtime
- BLE stack by [TrouBLE](https://github.com/embassy-rs/trouble)
- Board support from [microbit-bsp](https://github.com/lulf/microbit-bsp)
- Hardware by [micro:bit Educational Foundation](https://microbit.org)

## 📞 Support

Having issues? Check:
1. [QUICKSTART.md](QUICKSTART.md) - Quick reference
2. [BUTTON_TEST.md](BUTTON_TEST.md) - Testing and troubleshooting
3. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Additional testing methods
4. [BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md) - Technical details

---

**Ready to get started?** → [QUICKSTART.md](QUICKSTART.md)
