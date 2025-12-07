# Testing BLE Joystick on Linux

Complete guide for testing your micro:bit BLE joystick on a Linux laptop.

## 🔧 System Check

**Your system:**
- ✅ bluetoothctl v5.66 (installed)
- ✅ Python 3.11.2 (installed)
- ✅ Linux (Debian-based)

---

## 🚀 Quick Start Options

Choose your testing method:

| Method | Difficulty | Features | Time |
|--------|-----------|----------|------|
| **Web Bluetooth** | ⭐ Easy | Real-time GUI | 2 min |
| **bluetoothctl** | ⭐⭐ Medium | CLI, built-in | 5 min |
| **Python Script** | ⭐ Easy | Automated, logging | 5 min |
| **GUI Tools** | ⭐ Easy | Visual, user-friendly | 3 min |

---

## Option 1: Web Bluetooth (Recommended) ⭐

**Fastest and easiest!** Works in Chrome/Chromium/Edge.

### Step 1: Create Test HTML

```bash
cd /home/beattie/projects/docker-microbit-v2/ble-joystick
cat > ble-test.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>micro:bit Joystick Test</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            display: block;
            margin: 20px auto;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            text-align: center;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        .status.connected {
            background: #d4edda;
            color: #155724;
        }
        .values {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 30px 0;
        }
        .value-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .value-box h3 {
            margin: 0 0 10px 0;
            color: #666;
        }
        .value-display {
            font-size: 48px;
            font-weight: bold;
            color: #007bff;
            font-family: 'Courier New', monospace;
        }
        .joystick-visual {
            width: 300px;
            height: 300px;
            margin: 20px auto;
            position: relative;
            background: #e9ecef;
            border-radius: 50%;
            border: 3px solid #dee2e6;
        }
        .joystick-dot {
            width: 30px;
            height: 30px;
            background: #dc3545;
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            transition: all 0.1s;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
            font-size: 14px;
        }
        .stat-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-label {
            color: #666;
            font-size: 12px;
        }
        .stat-value {
            font-weight: bold;
            color: #333;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 micro:bit Joystick Test</h1>

        <div id="status" class="status disconnected">Not Connected</div>

        <button id="connectBtn">Connect to micro:bit</button>

        <div class="values">
            <div class="value-box">
                <h3>X-Axis</h3>
                <div class="value-display" id="x-value">---</div>
                <div style="font-size: 12px; color: #666; margin-top: 10px;">
                    <span id="x-percent">0%</span>
                </div>
            </div>
            <div class="value-box">
                <h3>Y-Axis</h3>
                <div class="value-display" id="y-value">---</div>
                <div style="font-size: 12px; color: #666; margin-top: 10px;">
                    <span id="y-percent">0%</span>
                </div>
            </div>
        </div>

        <div class="joystick-visual">
            <div class="joystick-dot" id="joystickDot"></div>
        </div>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">Updates</div>
                <div class="stat-value" id="updateCount">0</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Update Rate</div>
                <div class="stat-value" id="updateRate">0 Hz</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Latency</div>
                <div class="stat-value" id="latency">-- ms</div>
            </div>
        </div>

        <div style="margin-top: 30px; padding: 15px; background: #e7f3ff; border-radius: 5px; font-size: 14px;">
            <strong>Instructions:</strong>
            <ol style="margin: 10px 0;">
                <li>Click "Connect to micro:bit" button</li>
                <li>Select "microbit-joy" from the dialog</li>
                <li>Move the joystick and watch values update!</li>
            </ol>
            <p style="margin: 10px 0 0 0;"><strong>Expected Values:</strong> Center = 512, Range = 0-1023</p>
        </div>
    </div>

    <script>
        const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
        const X_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1';
        const Y_CHAR_UUID = '12345678-1234-5678-1234-56789abcdef2';

        let updateCount = 0;
        let lastUpdateTime = Date.now();
        let updateTimes = [];

        function updateStatus(message, connected) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + (connected ? 'connected' : 'disconnected');
        }

        function updateValue(axis, value) {
            const valueElement = document.getElementById(axis + '-value');
            const percentElement = document.getElementById(axis + '-percent');

            valueElement.textContent = value;
            const percent = ((value / 1023) * 100).toFixed(1);
            percentElement.textContent = percent + '%';

            // Update joystick visual
            updateJoystickVisual();

            // Update stats
            updateCount++;
            document.getElementById('updateCount').textContent = updateCount;

            const now = Date.now();
            const delta = now - lastUpdateTime;
            lastUpdateTime = now;

            // Calculate update rate (moving average)
            updateTimes.push(delta);
            if (updateTimes.length > 10) updateTimes.shift();
            const avgDelta = updateTimes.reduce((a, b) => a + b) / updateTimes.length;
            const rate = (1000 / avgDelta).toFixed(1);
            document.getElementById('updateRate').textContent = rate + ' Hz';
            document.getElementById('latency').textContent = delta + ' ms';
        }

        function updateJoystickVisual() {
            const xValue = parseInt(document.getElementById('x-value').textContent) || 512;
            const yValue = parseInt(document.getElementById('y-value').textContent) || 512;

            const dot = document.getElementById('joystickDot');

            // Convert 0-1023 to -135 to +135 pixels (300px diameter, leave margin)
            // Axes are inverted: higher value = left/up, lower = right/down
            const xPos = -((xValue - 512) / 512) * 135;  // Inverted: left = positive value
            const yPos = -((yValue - 512) / 512) * 135;  // Inverted: up = positive value

            dot.style.transform = `translate(calc(-50% + ${xPos}px), calc(-50% + ${yPos}px))`;
        }

        document.getElementById('connectBtn').addEventListener('click', async () => {
            try {
                const button = document.getElementById('connectBtn');
                button.disabled = true;
                button.textContent = 'Connecting...';

                updateStatus('Requesting device...', false);

                const device = await navigator.bluetooth.requestDevice({
                    filters: [{ name: 'microbit-joy' }],
                    optionalServices: [SERVICE_UUID]
                });

                updateStatus('Connecting to GATT server...', false);
                const server = await device.gatt.connect();

                updateStatus('Getting service...', false);
                const service = await server.getPrimaryService(SERVICE_UUID);

                updateStatus('Getting characteristics...', false);
                const xChar = await service.getCharacteristic(X_CHAR_UUID);
                const yChar = await service.getCharacteristic(Y_CHAR_UUID);

                // Read initial values
                const xInitial = await xChar.readValue();
                const yInitial = await yChar.readValue();
                updateValue('x', xInitial.getUint16(0, true));
                updateValue('y', yInitial.getUint16(0, true));

                // Setup notifications
                xChar.addEventListener('characteristicvaluechanged', (event) => {
                    const value = event.target.value.getUint16(0, true);
                    updateValue('x', value);
                });

                yChar.addEventListener('characteristicvaluechanged', (event) => {
                    const value = event.target.value.getUint16(0, true);
                    updateValue('y', value);
                });

                await xChar.startNotifications();
                await yChar.startNotifications();

                updateStatus('✓ Connected to micro:bit!', true);
                button.textContent = 'Connected';

                // Handle disconnection
                device.addEventListener('gattserverdisconnected', () => {
                    updateStatus('Disconnected', false);
                    button.disabled = false;
                    button.textContent = 'Connect to micro:bit';
                    document.getElementById('x-value').textContent = '---';
                    document.getElementById('y-value').textContent = '---';
                });

            } catch(error) {
                console.error('Error:', error);
                updateStatus('Error: ' + error.message, false);
                const button = document.getElementById('connectBtn');
                button.disabled = false;
                button.textContent = 'Connect to micro:bit';
            }
        });
    </script>
</body>
</html>
HTMLEOF

echo "✓ HTML test page created: ble-test.html"
```

**Note:** The visual joystick display accounts for hardware axis inversion:
- Higher values (>512) = LEFT/UP movement
- Lower values (<512) = RIGHT/DOWN movement

The red dot will move correctly to match your physical joystick direction.

### Step 2: Open in Browser

```bash
# Option A: Using default browser
xdg-open ble-test.html

# Option B: Specific browser
google-chrome ble-test.html      # Chrome
chromium ble-test.html            # Chromium
microsoft-edge ble-test.html      # Edge
```

### Step 3: Test!

1. Click **"Connect to micro:bit"**
2. Select **"microbit-joy"** from popup
3. Watch values update in real-time!

### NB
If Selecting **"microbit-joy"** with **chromium** produces _"Error: Cannot read properties of undefined (reading 'requestDevice')"_ try ```chromium --enable-features=WebBluetooth ble-test.html```

**Features:**
- ✅ Real-time X/Y values
- ✅ Visual joystick position
- ✅ Update rate and latency
- ✅ Percentage display
- ✅ Connection status

---

## Option 2: bluetoothctl (Command Line) ⭐⭐

**Good for debugging and scripting.**

### Quick Test Script

```bash
# Create automated test script
cat > test-ble.sh << 'EOF'
#!/bin/bash

echo "=================================="
echo "micro:bit BLE Joystick Test"
echo "=================================="
echo ""
echo "Starting Bluetooth scan..."
echo "Look for 'microbit-joy' in the output below"
echo ""

# Start bluetoothctl in background and capture output
(
echo "power on"
sleep 1
echo "scan on"
sleep 5
echo "scan off"
sleep 1
echo "quit"
) | bluetoothctl | grep -A 5 "microbit-joy"

echo ""
echo "=================================="
echo "Did you see 'microbit-joy' above?"
echo "=================================="
echo ""
echo "If YES: Run the interactive test with: ./test-ble-interactive.sh"
echo "If NO: Check that micro:bit is powered and BLE is advertising"
EOF

chmod +x test-ble.sh
```

### Run Quick Test

```bash
./test-ble.sh
```

**Expected output:**
```
[NEW] Device XX:XX:XX:XX:XX:XX microbit-joy
```

### Interactive Testing

```bash
# Start bluetoothctl
bluetoothctl

# In bluetoothctl prompt:
[bluetooth]# power on
[bluetooth]# scan on

# Wait until you see:
# [NEW] Device XX:XX:XX:XX:XX:XX microbit-joy

# Copy the MAC address (XX:XX:XX:XX:XX:XX) and:
[bluetooth]# scan off
[bluetooth]# connect XX:XX:XX:XX:XX:XX

# Once connected:
[bluetooth]# menu gatt
[bluetooth]# list-attributes XX:XX:XX:XX:XX:XX

# Find the X-Axis characteristic path (UUID ends in ...def1)
# It will look like: /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/service0010/char0011

# Select and read X-Axis:
[bluetooth]# select-attribute /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/service0010/char0011
[bluetooth]# read
# Should show: [00 02] (512 in little-endian)

# Enable notifications:
[bluetooth]# notify on
# Now move joystick - values will update automatically!

# To stop:
[bluetooth]# notify off
[bluetooth]# back
[bluetooth]# disconnect
[bluetooth]# quit
```

**Full walkthrough with your actual device:**

```bash
# I'll create an interactive helper script
cat > test-ble-interactive.sh << 'SHEOF'
#!/bin/bash

echo "========================================="
echo "micro:bit BLE Joystick Interactive Test"
echo "========================================="
echo ""
echo "Step 1: Starting Bluetooth and scanning..."

# Scan and get the MAC address
MAC=$(timeout 8 bluetoothctl <<< "power on
scan on" | grep -o '[0-9A-F]\{2\}:[0-9A-F]\{2\}:[0-9A-F]\{2\}:[0-9A-F]\{2\}:[0-9A-F]\{2\}:[0-9A-F]\{2\}.*microbit-joy' | head -1 | cut -d' ' -f1)

if [ -z "$MAC" ]; then
    echo "❌ Could not find microbit-joy"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Is micro:bit powered on?"
    echo "  2. Did firmware flash successfully?"
    echo "  3. Are LEDs blinking?"
    echo ""
    echo "Try running: bluetoothctl"
    echo "Then manually: power on"
    echo "              scan on"
    exit 1
fi

echo "✓ Found device: $MAC"
echo ""
echo "Step 2: Connecting to device..."

# Connect
bluetoothctl <<< "scan off
connect $MAC" &>/dev/null
sleep 3

echo "✓ Connected!"
echo ""
echo "Step 3: Reading values..."
echo ""
echo "To enable live notifications:"
echo ""
echo "  bluetoothctl"
echo "  connect $MAC"
echo "  menu gatt"
echo "  list-attributes"
echo "  # Find characteristic with UUID ending in ...def1 or ...def2"
echo "  select-attribute /org/bluez/hci0/dev_${MAC//:/_}/serviceXXXX/charXXXX"
echo "  notify on"
echo ""
echo "Device MAC: $MAC"
echo "Device path: /org/bluez/hci0/dev_${MAC//:/_}"
echo ""
SHEOF

chmod +x test-ble-interactive.sh
```

---

## Option 3: Python Script (Automated) ⭐

**Best for logging and automated testing.**

### Install Dependencies

```bash
# Install bleak (async BLE library)
pip3 install --user bleak
```

### Create Test Script

```bash
cat > test_joystick.py << 'PYEOF'
#!/usr/bin/env python3
"""
micro:bit BLE Joystick Test
Connects and displays real-time joystick values
"""

import asyncio
from bleak import BleakScanner, BleakClient
import struct
import time

# UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

class JoystickMonitor:
    def __init__(self):
        self.x_value = 512
        self.y_value = 512
        self.update_count = 0
        self.last_update = time.time()

    def x_callback(self, sender, data):
        """Called when X-axis value changes"""
        self.x_value = struct.unpack('<H', data)[0]  # Little-endian uint16
        self.update_count += 1
        self.print_values()

    def y_callback(self, sender, data):
        """Called when Y-axis value changes"""
        self.y_value = struct.unpack('<H', data)[0]
        self.update_count += 1
        self.print_values()

    def print_values(self):
        """Print current joystick state"""
        now = time.time()
        delta = now - self.last_update
        rate = 1.0 / delta if delta > 0 else 0
        self.last_update = now

        # Determine direction
        x_dir = "CENTER"
        if self.x_value > 600:
            x_dir = "LEFT"
        elif self.x_value < 400:
            x_dir = "RIGHT"

        y_dir = "CENTER"
        if self.y_value > 600:
            y_dir = "UP"
        elif self.y_value < 400:
            y_dir = "DOWN"

        # Create visual bar
        x_bar = self.value_bar(self.x_value)
        y_bar = self.value_bar(self.y_value)

        print(f"\r[{self.update_count:4d}] "
              f"X: {self.x_value:4d} {x_bar} {x_dir:6s} | "
              f"Y: {self.y_value:4d} {y_bar} {y_dir:6s} | "
              f"{rate:4.1f} Hz   ", end='', flush=True)

    @staticmethod
    def value_bar(value, width=20):
        """Create ASCII bar graph"""
        pos = int((value / 1023) * width)
        bar = ['─'] * width
        bar[width // 2] = '┼'  # Center marker
        bar[pos] = '█'
        return ''.join(bar)

async def main():
    print("=========================================")
    print("micro:bit BLE Joystick Test")
    print("=========================================")
    print()
    print("Scanning for 'microbit-joy'...")

    # Scan for device
    device = None
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        if d.name == "microbit-joy":
            device = d
            break

    if not device:
        print("❌ Could not find 'microbit-joy'")
        print("\nTroubleshooting:")
        print("  1. Is micro:bit powered on?")
        print("  2. Is BLE firmware running?")
        print("  3. Are LEDs blinking?")
        return

    print(f"✓ Found device: {device.name} ({device.address})")
    print()
    print("Connecting...")

    monitor = JoystickMonitor()

    async with BleakClient(device.address) as client:
        print(f"✓ Connected to {device.name}!")
        print()

        # Read initial values
        x_initial = await client.read_gatt_char(X_CHAR_UUID)
        y_initial = await client.read_gatt_char(Y_CHAR_UUID)

        monitor.x_value = struct.unpack('<H', x_initial)[0]
        monitor.y_value = struct.unpack('<H', y_initial)[0]

        print(f"Initial values: X={monitor.x_value}, Y={monitor.y_value}")
        print()
        print("Enabling notifications...")
        print("Move the joystick to see live updates!")
        print("Press Ctrl+C to exit")
        print()
        print("─" * 80)

        # Enable notifications
        await client.start_notify(X_CHAR_UUID, monitor.x_callback)
        await client.start_notify(Y_CHAR_UUID, monitor.y_callback)

        try:
            # Keep running until Ctrl+C
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n" + "─" * 80)
            print(f"\nTotal updates received: {monitor.update_count}")
            print("Disconnecting...")
            await client.stop_notify(X_CHAR_UUID)
            await client.stop_notify(Y_CHAR_UUID)

    print("✓ Disconnected")
    print("\nTest complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
PYEOF

chmod +x test_joystick.py
```

### Run Python Test

```bash
./test_joystick.py
```

**Expected output:**
```
=========================================
micro:bit BLE Joystick Test
=========================================

Scanning for 'microbit-joy'...
✓ Found device: microbit-joy (XX:XX:XX:XX:XX:XX)

Connecting...
✓ Connected to microbit-joy!

Initial values: X=512, Y=512

Enabling notifications...
Move the joystick to see live updates!
Press Ctrl+C to exit

────────────────────────────────────────
[  42] X:  512 ──────────█─────────── CENTER | Y:  512 ──────────█─────────── CENTER | 10.2 Hz
```

---

## Option 4: GUI Tools ⭐

### Install Bluetooth Manager

```bash
# Install GUI tool
sudo apt install blueman

# Launch
blueman-manager
```

**Steps:**
1. Click "Search" to scan
2. Find "microbit-joy"
3. Right-click → Connect
4. Right-click → Setup → Serial Port

**Note:** GUI tools often don't support GATT notifications well. **Web Bluetooth or Python script recommended instead.**

---

## 🔍 Verification Checklist

### Pre-Test
- [ ] micro:bit connected via USB
- [ ] Firmware flashed successfully (`cargo run --release`)
- [ ] LEDs blinking (startup + slow blink)
- [ ] Laptop Bluetooth enabled

### Quick Check
```bash
# Check Bluetooth status
bluetoothctl show

# Should show:
#   Powered: yes
#   Discoverable: yes
```

### Scanning
- [ ] Device appears as "microbit-joy"
- [ ] Can see MAC address
- [ ] Signal strength adequate (RSSI > -80)

### Connection
- [ ] Can connect successfully
- [ ] Service discovered (UUID: 12345678...)
- [ ] Two characteristics visible
- [ ] Can enable notifications

### Values
- [ ] Center reads ~512 on both axes
- [ ] X changes when moving left/right
- [ ] Y changes when moving up/down
- [ ] Range 0-1023 achievable
- [ ] Update rate ~10 Hz

---

## 🐛 Troubleshooting

### Device Not Found

```bash
# Check if Bluetooth is working
hciconfig

# Should show hci0 UP RUNNING

# If not:
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Restart Bluetooth
sudo systemctl restart bluetooth

# Check again
bluetoothctl show
```

### Permission Denied

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Log out and back in, or:
newgrp bluetooth
```

### Connection Fails

```bash
# Remove cached device
bluetoothctl

[bluetooth]# devices
# Note the MAC address of microbit-joy

[bluetooth]# remove XX:XX:XX:XX:XX:XX
[bluetooth]# scan on
# Wait for device to appear
[bluetooth]# scan off
[bluetooth]# pair XX:XX:XX:XX:XX:XX
[bluetooth]# connect XX:XX:XX:XX:XX:XX
```

### Python Script Issues

```bash
# Install bleak
pip3 install --user bleak

# Check installation
python3 -c "import bleak; print(bleak.__version__)"

# If still fails, use system Python:
sudo apt install python3-pip
sudo pip3 install bleak
```

---

## 📊 Performance Testing

### Measure Update Rate

```bash
# Using Python script - watch the Hz value
./test_joystick.py
# Move joystick continuously
# Should see ~10 Hz

# Using bluetoothctl with timestamps
bluetoothctl <<EOF | ts
connect XX:XX:XX:XX:XX:XX
menu gatt
select-attribute <CHAR_PATH>
notify on
EOF
```

### Log Data

```bash
# Log to file with Python
./test_joystick.py | tee joystick_log.txt

# Or with bluetoothctl
bluetoothctl 2>&1 | tee ble_log.txt
```

---

## 📈 Quick Comparison

| Method | Setup Time | Real-time | Logging | Automation | Recommended For |
|--------|-----------|-----------|---------|------------|----------------|
| Web Bluetooth | 2 min | ✅ Great | ❌ No | ❌ No | Quick testing, visual feedback |
| bluetoothctl | 2 min | ✅ Good | ⚠️ Manual | ⚠️ Scriptable | Debugging, low-level |
| Python Script | 5 min | ✅ Great | ✅ Yes | ✅ Yes | Automated testing, logging |
| GUI Tools | 3 min | ⚠️ Limited | ❌ No | ❌ No | Simple connect/disconnect |

---

## 🚀 Recommended Testing Flow

### First Time (5 minutes)
1. **Flash firmware**: `cargo run --release`
2. **Quick test**: Open `ble-test.html` in Chrome
3. **Connect and verify**: Move joystick, watch values

### Regular Testing (2 minutes)
1. **Run Python script**: `./test_joystick.py`
2. **Move joystick**: Verify all directions
3. **Check update rate**: Should be ~10 Hz

### Debugging (10 minutes)
1. **Monitor logs**: `probe-rs run ...`
2. **Test with bluetoothctl**: Manual GATT interaction
3. **Check with Python**: Automated value logging

---

## 🎯 Success Indicators

All these should work:

✅ `bluetoothctl scan on` shows "microbit-joy"
✅ Can connect without errors
✅ Web Bluetooth page connects instantly
✅ Python script shows ~10 Hz update rate
✅ Values respond to joystick movement
✅ Can disconnect and reconnect

---

## 📝 Next Steps

Once testing works:
1. **Collect data**: Use Python script to log movements
2. **Build an app**: Use the values to control something
3. **Add features**: Button press, battery level, etc.
4. **Optimize**: Adjust update rate, connection parameters

---

**Ready to test?** Start with Web Bluetooth - it's the fastest!

```bash
xdg-open ble-test.html
```

Or use Python for automated testing:

```bash
pip3 install --user bleak
./test_joystick.py
```
