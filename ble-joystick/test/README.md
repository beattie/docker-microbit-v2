# BLE Joystick Test Tools

This directory contains test utilities for the micro:bit BLE joystick + button project.

## Files

### `ble-test.html`
Web Bluetooth test interface with visual joystick and button display.

**Usage:**
```bash
# Chromium (requires flag)
chromium --enable-features=WebBluetooth ble-test.html

# Firefox (works by default)
firefox ble-test.html
```

**Features:**
- Real-time joystick position visualization
- Button A/B press indicators with animations
- Connects to "microbit-joy" BLE device
- Subscribes to all 4 characteristics (X, Y, Button A, Button B)

---

### `test_buttons.py`
Python script for programmatic BLE testing using the `bleak` library.

**Setup:**
```bash
pip install bleak
```

**Usage:**
```bash
python3 test_buttons.py
```

**Features:**
- Scans and connects to "microbit-joy" automatically
- Reads initial values from all characteristics
- Subscribes to notifications
- Real-time console output for joystick and button events
- Proper u16/u8 data parsing

---

## BLE Service Details

**Service UUID:** `12345678-1234-5678-1234-56789abcdef0`

**Characteristics:**
- `...def1` - X-axis (u16, little-endian, READ + NOTIFY)
- `...def2` - Y-axis (u16, little-endian, READ + NOTIFY)
- `...def3` - Button A (u8, 0=released, 1=pressed, READ + NOTIFY)
- `...def4` - Button B (u8, 0=released, 1=pressed, READ + NOTIFY)

---

## Troubleshooting

**Device not found:**
1. Check micro:bit is powered on
2. Verify firmware is flashed: `cargo flash --release --chip nRF52833_xxAA`
3. Check RTT logs show "[BLE] Advertising..."
4. Restart Bluetooth: `sudo systemctl restart bluetooth`

**Web Bluetooth not available:**
- Use Chromium with `--enable-features=WebBluetooth` flag
- Or use Firefox (Web Bluetooth enabled by default)

**Python script fails:**
- Install bleak: `pip install bleak`
- Check permissions: May need to add user to `bluetooth` group
- Verify Bluetooth adapter is enabled

---

For complete testing instructions, see [BUTTON_TEST.md](../BUTTON_TEST.md)
