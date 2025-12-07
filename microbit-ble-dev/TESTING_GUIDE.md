# BLE Joystick Testing Guide

## Build Status ✅

**Binary Information:**
- **Location**: `target/thumbv7em-none-eabihf/release/ble-joystick`
- **Size**: 2.5MB (with debug info, will be stripped when flashed)
- **Flash Usage**: ~138KB code + 4.8KB data = ~143KB total
- **RAM Usage**: ~39KB + ~5KB = ~44KB total
- **Target**: ARM Cortex-M4 (nRF52833)

**Memory Fit Check:**
- ✅ Flash: 143KB used / 512KB available (28%)
- ✅ RAM: 44KB used / 128KB available (34%)

---

## Hardware Requirements

### Essential
- **micro:bit v2** with nRF52833 chip
- **Joystick:bit** or compatible analog joystick on pins P1 (X) and P2 (Y)
- **USB cable** for programming and power

### For Programming
One of the following:
- **Built-in USB** (micro:bit v2 has onboard debugger)
- **J-Link** debug probe (optional, faster)
- **DAPLink** compatible probe

### For Testing
- **Smartphone** with BLE:
  - Android 4.3+ with nRF Connect app
  - iOS 10+ with LightBlue app
- OR **Computer** with BLE:
  - macOS with LightBlue
  - Linux with bluetoothctl
  - Windows 10+ with nRF Connect

---

## Step 1: Flashing the Firmware

### Option A: Using probe-rs (Recommended)

**Install probe-rs** (if not already installed):
```bash
# macOS
brew install probe-rs

# Linux
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/probe-rs/probe-rs/releases/latest/download/probe-rs-tools-installer.sh | sh

# Windows
# Download installer from: https://probe.rs/docs/getting-started/installation/
```

**Flash the firmware**:
```bash
# Connect micro:bit via USB
# The .cargo/config.toml is already configured with the runner

# Method 1: Using cargo run (recommended)
cargo run --release

# Method 2: Using probe-rs directly
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Method 3: Flash without running
probe-rs download --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick
```

**Expected Output:**
```
     Erasing ✔ [00:00:01] [##########] 143.00 KiB/143.00 KiB @ 95.33 KiB/s (eta 0s )
 Programming ✔ [00:00:02] [##########] 143.00 KiB/143.00 KiB @ 67.45 KiB/s (eta 0s )
    Finished in 3.2s
=================================
micro:bit v2 BLE Joystick
=================================
Initializing peripherals...
✓ LED task spawned
Spawning joystick task...
✓ Joystick task spawned
Initializing BLE stack...
✓ MPSL task spawned
BLE Address: Address::Random([0x41, 0x5A, 0xE3, 0x1E, 0x10, 0xC9])
✓ BLE Host stack created
=================================
✓ All tasks running!
=================================
✓ LED matrix initialized
Starting LED startup sequence...
Startup blink 1/3
...
```

### Option B: Using cargo-embed

```bash
# Install cargo-embed
cargo install cargo-embed

# Flash and monitor
cargo embed --release
```

### Option C: Using pyOCD (Alternative)

```bash
# Install pyOCD
pip install pyocd

# Flash
pyocd flash -t nrf52833 target/thumbv7em-none-eabihf/release/ble-joystick
```

---

## Step 2: Verify Operation

### Visual Indicators

**LED Behavior:**
1. **Startup**: Top row blinks 3 times quickly (startup sequence)
2. **Running**: Top row blinks slowly (500ms on, 500ms off)

**If LEDs don't blink:**
- Check USB power connection
- Check firmware flashed successfully
- Try resetting the micro:bit (button on back)

### Serial Output (Optional)

**Monitor logs with probe-rs:**
```bash
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick
```

**Expected log output:**
```
✓ LED matrix initialized
✓ ADC channels configured
Calibrating joystick center position...
Please do not touch the joystick during calibration...
✓ Calibration complete: X_center=1850, Y_center=1920
Starting joystick readings (reading every 100ms)...
[BLE] Creating GATT server...
[BLE] GATT server created
[BLE] Advertising as 'microbit-joy'...
```

---

## Step 3: Testing with BLE Scanner Apps

### Option 1: nRF Connect (Android/iOS) - **Recommended**

**Installation:**
- Android: [Google Play Store](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp)
- iOS: [App Store](https://apps.apple.com/app/nrf-connect-for-mobile/id1054362403)

**Testing Steps:**

1. **Open nRF Connect**
   - Launch the app
   - Grant Bluetooth and location permissions if requested

2. **Scan for Device**
   - Tap "SCAN" button
   - Look for device named **"microbit-joy"**
   - Should appear in "SCANNER" tab

3. **Connect**
   - Tap "CONNECT" next to microbit-joy
   - Wait for connection (status: "Connected")

4. **Discover Services**
   - App automatically discovers services
   - Look for **"Unknown Service"** with UUID `12345678...`

5. **View Characteristics**
   - Expand the unknown service
   - You should see two characteristics:
     - **Unknown Characteristic** (UUID: `12345678-1234-5678-1234-56789abcdef1`) - X-Axis
     - **Unknown Characteristic** (UUID: `12345678-1234-5678-1234-56789abcdef2`) - Y-Axis

6. **Enable Notifications**
   - Tap the **↓** (download/subscribe) icon on X-Axis characteristic
   - Tap the **↓** icon on Y-Axis characteristic
   - Icons should change to **↓** with checkmark

7. **Test Joystick**
   - Move joystick in different directions
   - Watch values update in real-time:
     - **Center**: Both ~512 (0x0200)
     - **Left**: X increases above 512
     - **Right**: X decreases below 512
     - **Up**: Y increases above 512
     - **Down**: Y decreases below 512
   - **Value format**: 16-bit unsigned integer (little-endian)
   - **Range**: 0-1023 (0x0000 to 0x03FF)

8. **Read Values**
   - Tap the **↑** (upload/read) icon to read current value
   - Values should match the latest notification

**Screenshot locations in nRF Connect:**
- Scan screen: Shows "microbit-joy" with signal strength
- Service screen: Shows UUID `12345678-1234-5678-1234-56789abcdef0`
- Characteristics: X (UUID ending ...def1), Y (UUID ending ...def2)

### Option 2: LightBlue (iOS/macOS)

**Installation:**
- iOS: [App Store](https://apps.apple.com/app/lightblue/id557428110)
- macOS: [App Store](https://apps.apple.com/app/lightblue/id639944780)

**Testing Steps:**

1. **Launch LightBlue**
   - Grant Bluetooth permissions

2. **Find Device**
   - "microbit-joy" appears in peripherals list
   - Shows signal strength (RSSI)

3. **Connect**
   - Tap on "microbit-joy"
   - Connection status shown at top

4. **Navigate to Service**
   - Scroll to **"Unknown Service"** (UUID: `12345678-...def0`)
   - Tap to expand

5. **View Characteristics**
   - **Characteristic 1**: X-Axis (UUID ending `...def1`)
   - **Characteristic 2**: Y-Axis (UUID ending `...def2`)

6. **Subscribe to Notifications**
   - Tap "Listen for notifications" on X-Axis
   - Tap "Listen for notifications" on Y-Axis

7. **Monitor Values**
   - Move joystick
   - Watch "Hex" and "UTF-8 / ASCII" fields update
   - Values shown as 2-byte hex (e.g., `00 02` = 512)

### Option 3: bluetoothctl (Linux CLI)

```bash
# Start bluetoothctl
bluetoothctl

# Scan for devices
[bluetooth]# scan on

# Look for micro:bit
# Device XX:XX:XX:XX:XX:XX microbit-joy

# Connect (replace with actual address)
[bluetooth]# connect XX:XX:XX:XX:XX:XX

# List services
[bluetooth]# menu gatt

# List attributes
[bluetooth]# list-attributes XX:XX:XX:XX:XX:XX

# Select characteristic (use UUID)
[bluetooth]# select-attribute /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/service0010/char0011

# Enable notifications
[bluetooth]# notify on

# Read value
[bluetooth]# read
```

### Option 4: Web Bluetooth (Chrome/Edge)

**Create a simple HTML test page:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>micro:bit Joystick Test</title>
</head>
<body>
    <h1>micro:bit Joystick BLE Test</h1>
    <button id="connect">Connect</button>
    <div id="status">Not connected</div>
    <div>X-Axis: <span id="x-value">---</span></div>
    <div>Y-Axis: <span id="y-value">---</span></div>

    <script>
        const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
        const X_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1';
        const Y_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef2';

        document.getElementById('connect').addEventListener('click', async () => {
            try {
                const device = await navigator.bluetooth.requestDevice({
                    filters: [{ name: 'microbit-joy' }],
                    optionalServices: [SERVICE_UUID]
                });

                const server = await device.gatt.connect();
                document.getElementById('status').textContent = 'Connected!';

                const service = await server.getPrimaryService(SERVICE_UUID);

                const xChar = await service.getCharacteristic(X_CHAR_UUID);
                const yChar = await service.getCharacteristic(Y_CHAR_UUID);

                xChar.addEventListener('characteristicvaluechanged', (event) => {
                    const value = event.target.value.getUint16(0, true);
                    document.getElementById('x-value').textContent = value;
                });

                yChar.addEventListener('characteristicvaluechanged', (event) => {
                    const value = event.target.value.getUint16(0, true);
                    document.getElementById('y-value').textContent = value;
                });

                await xChar.startNotifications();
                await yChar.startNotifications();

            } catch(error) {
                console.error('Error:', error);
                document.getElementById('status').textContent = 'Error: ' + error;
            }
        });
    </script>
</body>
</html>
```

**Usage:**
1. Save as `joystick-test.html`
2. Open in Chrome/Edge (requires HTTPS in production)
3. Click "Connect"
4. Select "microbit-joy" from dialog
5. Watch values update

---

## Step 4: Validate Functionality

### Test Checklist

- [ ] **Device Advertising**
  - [ ] "microbit-joy" appears in BLE scanner
  - [ ] Can connect to device
  - [ ] Connection is stable

- [ ] **GATT Service**
  - [ ] Custom service UUID visible
  - [ ] Two characteristics present
  - [ ] Can read both characteristics

- [ ] **Notifications**
  - [ ] Can enable notifications on X-Axis
  - [ ] Can enable notifications on Y-Axis
  - [ ] Values update in real-time

- [ ] **Joystick Response**
  - [ ] Center position reads ~512 on both axes
  - [ ] X-Axis changes when moving left/right
  - [ ] Y-Axis changes when moving up/down
  - [ ] Full range achievable (0-1023)
  - [ ] Values return to center when released

- [ ] **Disconnection**
  - [ ] Can disconnect from client
  - [ ] Device returns to advertising
  - [ ] Can reconnect successfully

### Expected Values Reference

| Joystick Position | X-Axis | Y-Axis |
|-------------------|--------|--------|
| Center            | ~512   | ~512   |
| Full Left         | >900   | ~512   |
| Full Right        | <100   | ~512   |
| Full Up           | ~512   | >900   |
| Full Down         | ~512   | <100   |
| Top-Left          | >900   | >900   |
| Bottom-Right      | <100   | <100   |

**Note**: Exact values depend on your joystick hardware. The axes are inverted (positive = left/up).

---

## Troubleshooting

### Device Not Appearing in Scan

**Possible Causes:**
1. Firmware not running
2. BLE stack initialization failed
3. Bluetooth disabled on phone/computer
4. Out of range (try moving closer)

**Solutions:**
```bash
# Check if firmware is running (look for LED blinks)
# Reset micro:bit (button on back)

# View logs to check BLE initialization
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Look for these log lines:
# "✓ MPSL task spawned"
# "[BLE] Advertising as 'microbit-joy'..."
```

### Connection Fails

**Solutions:**
- Reset micro:bit
- Ensure no other device is connected
- Close and reopen BLE scanner app
- Turn Bluetooth off/on on your device
- Try different BLE scanner app

### No Notifications Received

**Check:**
1. Notifications are enabled (CCCD written)
2. Joystick is actually moving
3. Connection is still active

**Debug:**
```bash
# Monitor logs to see if joystick is being read
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick

# Should see:
# "Joy X: X=512 (raw=1850 delta=0 c=0), Y=512 (raw=1920 delta=0 c=0)"
```

### Values Don't Change

**Possible Issues:**
1. Joystick not connected to correct pins
2. Joystick power not connected
3. Faulty joystick hardware
4. Notification task not running

**Verify Hardware:**
- X-Axis must be on **Pin P1** (GPIO P0.03)
- Y-Axis must be on **Pin P2** (GPIO P0.04)
- Joystick VCC to 3.3V
- Joystick GND to GND

### Calibration Issues

If joystick center is not at 512:
1. **Don't touch joystick during startup** (calibration happens in first 100ms)
2. **Re-flash and don't move joystick** until calibration complete
3. Check logs for calibration values:
   ```
   ✓ Calibration complete: X_center=XXXX, Y_center=YYYY
   ```

### Build Errors

```bash
# Clean and rebuild
cargo clean
cargo build --release

# Ensure toolchain is installed
rustup target add thumbv7em-none-eabihf

# Check dependency versions
cargo tree | grep -E "trouble|embassy|microbit"
```

---

## Performance Monitoring

### Check Update Rate

**Using nRF Connect:**
- Enable notifications
- Count updates per second in notification log
- Should see ~10 updates/second (100ms interval)

### Check Connection Quality

**Metrics to observe:**
- **RSSI**: Signal strength (higher is better, typically -40 to -80 dBm)
- **Connection Interval**: Time between updates
- **Latency**: Time from joystick move to notification received

**In nRF Connect:**
- Tap connected device
- View "Connection Parameters"
- Check "Connection Interval" and "Supervision Timeout"

---

## Next Steps After Testing

Once basic functionality is verified:

1. **Build a Custom App**
   - Flutter/React Native mobile app
   - Web Bluetooth dashboard
   - Game controller interface

2. **Add Features**
   - Button press detection
   - Battery level reporting
   - Configurable sensitivity

3. **Optimize**
   - Adjust notification interval
   - Tune connection parameters
   - Reduce power consumption

4. **Implement HID**
   - Make device appear as standard gamepad
   - Works with games without custom software

---

## Additional Resources

### BLE Scanner Apps
- **nRF Connect**: https://www.nordicsemi.com/Products/Development-tools/nrf-connect-for-mobile
- **LightBlue**: https://punchthrough.com/lightblue/

### Development Tools
- **probe-rs**: https://probe.rs/
- **Web Bluetooth**: https://web.dev/bluetooth/

### Documentation
- **Nordic nRF52833**: https://www.nordicsemi.com/products/nrf52833
- **Bluetooth GATT**: https://www.bluetooth.com/specifications/specs/
- **Embassy**: https://embassy.dev/

---

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review BLE_IMPLEMENTATION.md for architecture details
3. Check logs with `probe-rs run`
4. Verify hardware connections
5. Try with different BLE scanner app

**Common Success Indicators:**
- ✅ LEDs blinking on startup and during operation
- ✅ "microbit-joy" visible in BLE scan
- ✅ Can connect without errors
- ✅ Notifications enabled successfully
- ✅ Values update when joystick moves

Happy testing! 🎮
