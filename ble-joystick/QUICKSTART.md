# Quick Start Guide - BLE Joystick

## ⚡ 3-Minute Flash & Test

### Prerequisites Check ✅
- [x] micro:bit v2 connected via USB
- [x] probe-rs installed (v0.29.1 ✓)
- [x] cargo-embed installed (v0.29.1 ✓)
- [x] Joystick:bit connected to P1 (X) and P2 (Y)
- [x] Smartphone with nRF Connect app installed

---

## Step 1: Flash (30 seconds)

```bash
# Option A: Fastest method
cargo run --release

# Option B: With monitoring
cargo embed --release
```

**Expected Output:**
```
Programming ✔ [##########] 143 KiB @ 67 KiB/s
=================================
micro:bit v2 BLE Joystick
=================================
✓ All tasks running!
[BLE] Advertising as 'microbit-joy'...
```

**LED Indicator:**
- 3 quick blinks → Startup
- Slow blink → Running

---

## Step 2: Connect (1 minute)

### On Your Phone:

1. **Open nRF Connect app**
2. **Tap SCAN**
3. **Find "microbit-joy"**
4. **Tap CONNECT**

---

## Step 3: Test (1 minute)

### Enable Notifications:

1. **Expand "Unknown Service"** (UUID: 12345678...)
2. **Tap ↓ button** on both characteristics
3. **Move joystick** → Watch values change!

### Expected Values:
- **Center**: X=512, Y=512
- **Left**: X>512
- **Right**: X<512
- **Up**: Y>512
- **Down**: Y<512

---

## Troubleshooting One-Liners

```bash
# Not advertising? Check logs:
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Connection issues? Rebuild:
cargo clean && cargo build --release && cargo run --release

# Wrong values? Recalibrate (don't touch joystick during startup):
# Reset micro:bit with button on back, wait for startup blinks
```

---

## What's Running?

```
┌──────────────┐
│  LED Blink   │ ← Top row flashing
├──────────────┤
│ Joystick ADC │ ← Reading P1 & P2 at 10Hz
├──────────────┤
│  BLE Stack   │ ← Advertising "microbit-joy"
├──────────────┤
│ Notifications│ ← Sending X/Y values
└──────────────┘
```

---

## System Status

✅ **Binary**: 2.5MB (143KB will be flashed)
✅ **Memory**: 28% Flash, 34% RAM
✅ **Tools**: probe-rs 0.29.1, cargo-embed 0.29.1
✅ **Target**: nRF52833 (micro:bit v2)

---

## Next Steps

📖 **Full Testing Guide**: See `TESTING_GUIDE.md` for:
- Web Bluetooth HTML example
- Advanced debugging
- Performance tuning
- Multiple BLE scanner apps

🔧 **Implementation Details**: See `BLE_IMPLEMENTATION.md` for:
- Architecture explanation
- Code walkthrough
- Future enhancements
- API documentation

📱 **Build an App**: Ready to create a custom controller app!

---

## Quick Commands Reference

```bash
# Flash & Run
cargo run --release              # Flash and monitor logs
cargo embed --release            # Flash with cargo-embed UI

# Build Only
cargo build --release            # Just compile

# Monitor Logs
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Check Binary Size
size target/thumbv7em-none-eabihf/release/ble-joystick

# Clean Build
cargo clean && cargo build --release
```

---

## Success Indicators

| Indicator | What It Means |
|-----------|---------------|
| 3 quick LED blinks | ✅ Startup successful |
| Slow LED blink | ✅ System running |
| "microbit-joy" in scan | ✅ BLE advertising |
| Connection successful | ✅ BLE stack working |
| Values update | ✅ Everything working! |

---

## That's It! 🎉

You now have a working BLE joystick. Move the joystick and watch the values update in real-time on your phone!

**Having issues?** Check `TESTING_GUIDE.md` for detailed troubleshooting.
