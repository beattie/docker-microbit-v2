# microbit-ble-dev - BLE & GATT Learning Project

A hands-on learning project for exploring Bluetooth Low Energy (BLE) and GATT features using Rust on the micro:bit v2. This project extends the ble-joystick foundation to demonstrate advanced BLE concepts through progressive implementation phases.

Much of the work in this project was performed by AI, specifically, Claude Code by Anthropic. One of the goals was to learn what AI could do. My primary goal had been to learn BLE and Rust. 
Unfortunately that did not work out and Claude actually did most of the work so that I missed out of the process of working through the process. I think I had hoped the process would be similar to a lecture, I did not find this to be the case. I found out what AI could do, I did not learn much about Rust and BLE.

I do hope to be able to go back over the code and the various phases to educate my self.

## 🎯 Project Purpose

This is a **learning and demonstration project** designed to:
- Master BLE and GATT protocol implementation in embedded Rust
- Explore Embassy async framework patterns
- Understand the TrouBLE BLE stack architecture
- Build practical experience with micro:bit v2 hardware
- Document BLE development best practices

**Base:** Forked from `ble-joystick` - a working BLE joystick implementation

## 📚 Learning Path

Follow the [LEARNING_PLAN.md](LEARNING_PLAN.md) for a structured 4-phase approach:

### Phase 1: Button GATT Characteristics
- Add Button A/B to GATT service
- Learn READ and NOTIFY properties
- Implement GPIO input handling
- Practice Embassy async tasks

### Phase 2: Code Modularization
- Refactor into logical modules
- Understand Rust visibility and module system
- Prepare for complex feature additions
- Follow embedded project organization patterns

### Phase 3: Standard Battery Service
- Implement Bluetooth SIG Battery Service
- Work with standard GATT UUIDs (16-bit)
- Read ADC internal voltage channels
- Handle multiple GATT services

### Phase 4: Runtime Configuration
- Implement WRITE characteristics
- Handle dynamic configuration updates
- Validate BLE input data
- Use Mutex for shared state management

## 🛠️ Hardware Requirements

- **[micro:bit v2](https://microbit.org)** - Nordic nRF52833 (ARM Cortex-M4)
- **[joystick:bit](https://wiki.elecfreaks.com/en/microbit/expansion-board/joystick-bit-v2/)** - Analog joystick expansion board
- **USB cable** for programming and power

## 🚀 Quick Start

```bash
# Navigate to project
cd microbit-ble-dev

# Build the project
cargo build --release

# Flash to micro:bit v2
cargo run --release
```

**Current State:** Working BLE joystick (inherited from ble-joystick)
- Real-time X/Y axis data via BLE notifications
- Auto-calibration on startup
- 10Hz update rate

## 📖 Documentation

### Learning Resources
- **[LEARNING_PLAN.md](LEARNING_PLAN.md)** - Comprehensive 4-phase implementation guide
- **[GATT.md](GATT.md)** - GATT fundamentals and protocol details
- **[BLE_IMPLEMENTATION.md](BLE_IMPLEMENTATION.md)** - Architecture and stack details
- **[RUST.md](RUST.md)** - Detailed code explanation and Rust patterns

### Practical Guides
- **[QUICKSTART.md](QUICKSTART.md)** - 3-minute setup and flash guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing with nRF Connect and mobile apps
- **[LINUX_TESTING.md](LINUX_TESTING.md)** - Linux-specific testing procedures
- **[BUTTON_TEST.md](BUTTON_TEST.md)** - Button testing procedures

## 🔧 Development Setup

**Prerequisites:**
```bash
# Install Rust embedded target
rustup target add thumbv7em-none-eabihf

# Install probe-rs for flashing
cargo install probe-rs-tools
```

**Recommended Workflow:**
```bash
# Create feature branch for each phase
git checkout -b phase-1-buttons

# Build and test
cargo build --release
cargo run --release

# Monitor logs with RTT
cargo embed --release
```

## 🧪 Testing Tools

**Mobile Apps:**
- **nRF Connect** (Android/iOS) - Nordic's comprehensive BLE testing tool
- **LightBlue** (iOS/macOS) - Simple GATT service browser

**Python Testing:**
```bash
cd test
python test_buttons.py  # Automated characteristic testing
```

**Web Bluetooth:**
```bash
# Open test/ble-test.html in Chrome/Edge
# Requires Web Bluetooth API support
```

## 📊 Current Features (ble-joystick base)

✅ **Implemented:**
- Real-time analog joystick (X/Y axes) via BLE
- Custom GATT service with READ and NOTIFY characteristics
- Automatic center-point calibration
- Embassy async task coordination
- LED status indicators
- Memory efficient (~28% flash, ~34% RAM)

## 🎯 Learning Objectives

By completing all 4 phases, you will understand:

**BLE/GATT Concepts:**
- GATT service and characteristic design
- Standard vs. custom UUIDs
- READ, WRITE, NOTIFY properties
- Connection lifecycle management
- Advertisement data encoding

**Embedded Rust:**
- Embassy async/await patterns
- Inter-task communication (Signal, Mutex)
- Hardware abstraction layers (HAL)
- ADC usage (analog and internal channels)
- GPIO configuration and reading

**Project Organization:**
- Module structure and visibility
- Embedded project architecture
- Resource sharing strategies
- Testing and validation approaches

## 🔌 GATT Service Specification (Current)

**Custom Joystick Service**
- Service UUID: `12345678-1234-5678-1234-56789abcdef0`

**Characteristics:**
| Name | UUID | Properties | Type | Range | Update Rate |
|------|------|------------|------|-------|-------------|
| X-Axis | `...def1` | Read, Notify | u16 | 0-1023 | 10Hz |
| Y-Axis | `...def2` | Read, Notify | u16 | 0-1023 | 10Hz |

**After Phase 1:** Add Button A (`...def3`) and Button B (`...def4`)

**After Phase 3:** Add Battery Service (UUID: `0x180F`)

**After Phase 4:** Add Configuration Service for runtime settings

## 🧩 Technology Stack

**Embedded Framework:**
- `embassy-executor` - Async task executor
- `embassy-time` - Timer and duration handling
- `embassy-sync` - Inter-task synchronization primitives
- `embassy-nrf` - nRF52833 hardware abstraction

**BLE Stack:**
- `trouble-host` - TrouBLE BLE stack (Nordic SoftDevice wrapper)
- `microbit-bsp` - micro:bit board support with TrouBLE integration

**Other:**
- `defmt` - Efficient embedded logging
- `heapless` - No-heap collections and strings
- `cortex-m` - ARM Cortex-M support

See [Cargo.toml](Cargo.toml) for complete dependencies.

## 📈 Performance Metrics

**Memory Usage (baseline):**
- Flash: 143KB / 512KB (28% - 356KB available after SoftDevice)
- RAM: 44KB / 128KB (34% - 85KB available after SoftDevice)

**Timing:**
- Joystick update rate: 10Hz (100ms intervals)
- Button polling: 50Hz (20ms intervals - planned Phase 1)
- BLE latency: ~50-100ms typical
- Battery updates: 60-second intervals (planned Phase 3)

## 🚧 Planned Extensions (Post-Learning Phases)

After completing the 4 learning phases, consider these advanced topics:

- **HID-over-GATT**: Implement standard Bluetooth gamepad profile
- **BLE Security**: Add pairing, bonding, and encryption
- **Multiple Connections**: Support 2-3 simultaneous clients
- **Power Optimization**: Low-power advertising, connection intervals
- **Data Logging**: Store metrics to internal flash
- **BLE Mesh**: Explore mesh networking capabilities

## 🎓 Learning Approach

This project is designed for **self-paced, hands-on learning**:

1. **Read** the learning plan phase objectives
2. **Understand** the technical references provided
3. **Implement** the features yourself (no copy-paste)
4. **Test** thoroughly using the provided test procedures
5. **Verify** with the phase completion checklists

**Philosophy:** Learn by doing - the plan provides guidance and references, but you write the code.

## 🤝 Credits

**Original Project:** ble-joystick by Brian Beattie
- Created as a BLE learning experience with AI assistance (Claude)
- Demonstrates practical embedded Rust and BLE implementation

**Built With:**
- [Embassy](https://embassy.dev/) - Modern embedded async framework
- [TrouBLE](https://github.com/embassy-rs/trouble) - Rust BLE stack
- [microbit-bsp](https://github.com/lulf/microbit-bsp) - micro:bit board support
- [micro:bit v2](https://microbit.org) - Educational hardware platform

## 📝 License

MIT or Apache-2.0 (your choice)

## 🔗 External Resources

**Official Documentation:**
- [Bluetooth SIG GATT Specs](https://www.bluetooth.com/specifications/specs/)
- [nRF52833 Datasheet](https://infocenter.nordicsemi.com/)
- [micro:bit v2 Tech Docs](https://tech.microbit.org/)

**Rust Embedded:**
- [Embassy Book](https://embassy.dev/book/)
- [Embedded Rust Book](https://rust-embedded.github.io/book/)

---

**Ready to start learning?** → Open [LEARNING_PLAN.md](LEARNING_PLAN.md) and begin Phase 1!
