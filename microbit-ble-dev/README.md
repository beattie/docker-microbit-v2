# BLE Joystick - micro:bit v2

A Bluetooth Low Energy (BLE) joystick implementation for the micro:bit v2, sending real-time analog joystick data wirelessly. Built with Rust using the Embassy async framework and TrouBLE BLE stack.

## 🎮 Features

- **Real-time BLE Notifications**: Joystick X/Y values transmitted at 10Hz
- **Custom GATT Service**: Standard BLE service with read and notify characteristics
- **Auto-calibration**: Centers joystick position on startup
- **Concurrent Tasks**: LED indicators, joystick reading, and BLE operations run simultaneously
- **Low Memory**: ~143KB flash, ~44KB RAM
- **Production Ready**: Based on official microbit-bsp examples

## 🚀 Quick Start

```bash
# Flash to your micro:bit v2
cargo run --release
```

See [QUICKSTART.md](QUICKSTART.md) for complete 3-minute setup guide.

## 📱 Testing

**On your smartphone:**
1. Install nRF Connect (Android/iOS) or LightBlue (iOS)
2. Scan for "microbit-joy"
3. Connect and enable notifications
4. Move joystick → Watch values update!

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed testing instructions.

## 🛠️ Hardware

- **[micro:bit v2](https://en.wikipedia.org/wiki/Micro_Bit)** - Nordic nRF52833 (Cortex-M4)
- **[joystick:bit](https://wiki.elecfreaks.com/en/microbit/expansion-board/joystick-bit-v2/)** - Analog joystick on P1 (X-axis) and P2 (Y-axis)
- **USB cable** for programming

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 3-minute flash and test guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing with multiple BLE apps
- **[BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md)** - Architecture and implementation details
- **[LINUX_TESTING.md](LINUX_TESTING.md)** Testing from a Linux system

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
| Characteristic | UUID | Properties | Type | Range |
|---------------|------|------------|------|-------|
| X-Axis | `...def1` | Read, Notify | u16 | 0-1023 |
| Y-Axis | `...def2` | Read, Notify | u16 | 0-1023 |

**Center Position**: X=512, Y=512 (calibrated at startup)

## 🧩 Dependencies

- `microbit-bsp = "0.4.0"` - Board support package with BLE
- `trouble-host = "0.2.0"` - BLE stack (TrouBLE)
- `embassy-executor`, `embassy-time`, `embassy-sync` - Async runtime
- `embassy-nrf = "0.4.1"` - nRF52833 HAL

See [Cargo.toml](Cargo.toml) for complete dependency list.

## 📈 Performance

- **Flash Usage**: 143KB / 512KB (28%)
- **RAM Usage**: 44KB / 128KB (34%)
- **Update Rate**: 10Hz (100ms interval)
- **BLE Latency**: ~50-100ms typical

## 🎯 Project Status

✅ **Implemented:**
- [x] Analog joystick reading with ADC
- [x] Automatic center calibration
- [x] BLE advertising and connection handling
- [x] Custom GATT service with notifications
- [x] Real-time data streaming
- [x] LED visual feedback
- [x] Comprehensive documentation

🚧 **Potential Enhancements:**
- [ ] HID-over-GATT (standard gamepad support)
- [ ] Button press detection
- [ ] Battery level reporting
- [ ] Connection status LED
- [ ] Configurable sensitivity
- [ ] Mobile app example

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
2. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Troubleshooting section
3. [BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md) - Technical details

---

**Ready to get started?** → [QUICKSTART.md](QUICKSTART.md)
