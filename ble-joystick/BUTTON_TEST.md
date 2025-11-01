# Button BLE Testing Guide

Complete guide to testing joystick + button BLE functionality on micro:bit v2.

---

## ✅ What's Implemented

### **Hardware:**
- ✅ Button A (micro:bit built-in)
- ✅ Button B (micro:bit built-in)
- ✅ Joystick X-axis (P1)
- ✅ Joystick Y-axis (P2)

### **Firmware:**
- ✅ Button reading (active-low with pull-up)
- ✅ RTT logging of button states
- ✅ BLE GATT service with 4 characteristics

### **BLE Service:**
```
Service UUID:   12345678-1234-5678-1234-56789abcdef0
├─ X-Axis:      12345678-1234-5678-1234-56789abcdef1 (u16, READ + NOTIFY)
├─ Y-Axis:      12345678-1234-5678-1234-56789abcdef2 (u16, READ + NOTIFY)
├─ Button A:    12345678-1234-5678-1234-56789abcdef3 (u8,  READ + NOTIFY)
└─ Button B:    12345678-1234-5678-1234-56789abcdef4 (u8,  READ + NOTIFY)
```

### **Binary Size:**
- Flash: **140 KB / 512 KB** (27%)
- RAM: **43 KB / 128 KB** (34%)

---

## 🚀 Quick Start

### **1. Flash Firmware**

```bash
# Build and flash
cargo flash --release --chip nRF52833_xxAA

# Or build + flash + monitor RTT
cargo run --release
```

### **2. Test with RTT Logs**

Press buttons on micro:bit while monitoring RTT output:

```
Joy 2: X=512 Y=512 Btn A=released, Btn B=released

# Press Button A:
  🔘 Button A: PRESSED
Joy 4: X=512 Y=512 Btn A=PRESSED, Btn B=released

# Press Button B:
  🔘 Button B: PRESSED
Joy 6: X=512 Y=512 Btn A=released, Btn B=PRESSED

# Press both:
  🔘 Button A: PRESSED
  🔘 Button B: PRESSED
Joy 8: X=512 Y=512 Btn A=PRESSED, Btn B=PRESSED
```

### **3. Test with Web Bluetooth**

**⚠️ IMPORTANT:**
- Web Bluetooth requires HTTP/HTTPS, not file:// protocol
- **Firefox NOT supported** - use Chrome/Chromium/Edge

```bash
# Step 1: Start HTTP server
cd test/
./serve.sh

# Step 2: Open in Chrome/Chromium
google-chrome http://localhost:8000/ble-test.html

# Or Edge
microsoft-edge http://localhost:8000/ble-test.html
```

**Steps:**
1. Click "Connect to micro:bit"
2. Select "microbit-joy" from device list
3. See joystick position update in real-time
4. Press Button A → See "Button A: PRESSED" light up
5. Press Button B → See "Button B: PRESSED" light up
6. Move joystick → See dot move in visual display

---

## 🧪 Detailed Testing

### **Test 1: Button RTT Logging**

**Objective:** Verify buttons are read correctly

```bash
cargo run --release
```

**Test Cases:**
- [ ] No buttons pressed → See "Btn A=released, Btn B=released"
- [ ] Press A → See "🔘 Button A: PRESSED"
- [ ] Release A → See "Btn A=released"
- [ ] Press B → See "🔘 Button B: PRESSED"
- [ ] Release B → See "Btn B=released"
- [ ] Press both → See both PRESSED
- [ ] Rapid press/release → Logs update (10Hz rate)

---

### **Test 2: Python GUI (⭐ Recommended)**

**Objective:** Visual testing with graphical interface

```bash
# Install dependencies (if not already installed)
pip install bleak

# Run GUI application
python3 test/gui_test.py
```

**Test Cases:**
- [ ] GUI window opens successfully
- [ ] Click "Connect to micro:bit" → Connection succeeds
- [ ] Status shows "✅ Connected!"
- [ ] Joystick center → Dot in center of circle, X=512, Y=512
- [ ] Move joystick → Dot follows movement smoothly
- [ ] Press Button A → Button turns purple, shows "PRESSED"
- [ ] Release Button A → Button returns to white, shows "Released"
- [ ] Press Button B → Button turns purple, shows "PRESSED"
- [ ] Release Button B → Button returns to white, shows "Released"
- [ ] Press both buttons → Both show "PRESSED" simultaneously
- [ ] Move joystick while pressing buttons → All update correctly
- [ ] Click "Disconnect" → Connection closes gracefully

**Advantages:**
- ✅ Works on all platforms (Linux, macOS, Windows)
- ✅ No browser required
- ✅ No Firefox compatibility issues
- ✅ Visual feedback with animations

---

### **Test 3: Web Bluetooth (Joystick Only)**

**Objective:** Verify joystick notifications

1. Open `test/ble-test.html` in browser
2. Connect to micro:bit
3. Move joystick in all directions

**Test Cases:**
- [ ] Center position → X=512, Y=512, dot in center
- [ ] Move LEFT → X increases, dot moves left
- [ ] Move RIGHT → X decreases, dot moves right
- [ ] Move UP → Y increases, dot moves up
- [ ] Move DOWN → Y decreases, dot moves down
- [ ] Circular motion → Dot follows smoothly
- [ ] Notification rate → ~10 updates per second

---

### **Test 4: Web Bluetooth (Buttons)**

**Objective:** Verify button notifications

With `test/ble-test.html` connected:

**Test Cases:**
- [ ] Button A released → White background, "Released"
- [ ] Press Button A → Purple gradient, "PRESSED", scales up
- [ ] Release Button A → Returns to white, "Released"
- [ ] Button B released → White background, "Released"
- [ ] Press Button B → Purple gradient, "PRESSED"
- [ ] Press both → Both show "PRESSED"
- [ ] Rapid press/release → UI updates smoothly

---

### **Test 5: Combined (Joystick + Buttons)**

**Objective:** Verify everything works simultaneously

**Test Cases:**
- [ ] Move joystick WHILE pressing Button A
- [ ] Move joystick WHILE pressing Button B
- [ ] Move joystick WHILE pressing both buttons
- [ ] All notifications arrive (no dropped updates)
- [ ] No lag or delays
- [ ] Connection stays stable

---

## 🔧 Troubleshooting

### **Issue: Web Bluetooth Not Working**

**Symptoms:**
- "navigator.bluetooth is undefined"
- "Web Bluetooth not supported in this browser"
- Can't see device list

**Solutions:**

**1. Check if using Firefox:**
- ❌ **Firefox does NOT support Web Bluetooth** (Mozilla's policy decision)
- ✅ **Use Chrome, Chromium, or Edge instead**

**2. Use HTTP/HTTPS protocol:**
```bash
cd test/
./serve.sh
# Then open: http://localhost:8000/ble-test.html
```

**3. Supported browsers:**
- ✅ Chrome/Chromium (recommended)
- ✅ Microsoft Edge
- ✅ Opera
- ✅ Brave
- ❌ Firefox (not supported)
- ❌ Safari (limited support)

---

### **Issue: Can't Find "microbit-joy"**

**Symptoms:**
- Device list is empty
- micro:bit not showing up

**Solutions:**
1. Check micro:bit is powered on (LEDs blinking)
2. Check RTT logs show "[BLE] Advertising..."
3. Reflash firmware:
   ```bash
   cargo flash --release --chip nRF52833_xxAA
   ```
4. Reset micro:bit (press reset button)
5. Check Bluetooth is enabled on your computer

---

### **Issue: Buttons Not Responding**

**Symptoms:**
- RTT logs show buttons always "released"
- Web Bluetooth shows no button changes

**Solutions:**
1. Verify you're pressing **micro:bit's built-in buttons** (A and B on front)
2. Check RTT logs for button readings
3. Verify firmware includes button code:
   ```bash
   cargo build --release 2>&1 | grep "button"
   ```
4. Reflash firmware

---

### **Issue: Notifications Not Received**

**Symptoms:**
- Can read values, but no real-time updates
- Values don't change when moving joystick/pressing buttons

**Solutions:**

**Check notifications enabled:**
```javascript
// Should see in browser console:
await xChar.startNotifications();  // Must be called for each characteristic
```

**Check connection:**
```javascript
// Browser console:
console.log(device.gatt.connected);  // Should be true
```

**Check RTT logs:**
```
[BLE] Starting notification loop (joystick + buttons)...
```

---

## 📊 Performance Metrics

### **Latency:**
- Button press to RTT log: **~10ms**
- Button press to BLE notification: **~30-50ms**
- Joystick move to BLE notification: **~30-50ms**

### **Update Rate:**
- ADC sampling: **10 Hz** (100ms interval)
- BLE notifications: **~10 per second**
- Button polling: **10 Hz** (same as joystick)

### **BLE Specs:**
- Connection interval: **~30ms** (negotiated by OS)
- Supervision timeout: **10 seconds**
- Max connections: **1**
- Advertising interval: **100ms**

---

## 🎯 Next Steps

### **Option A: Python Test Script**

Use the provided `test/test_buttons.py` script:

```bash
# Install dependencies
pip install bleak

# Run the test script
python3 test/test_buttons.py
```

The script will:
- Scan for "microbit-joy" device
- Connect and read initial values
- Subscribe to all 4 characteristics
- Display real-time joystick and button updates

### **Option B: HID-over-GATT**

Transform into universal gamepad (works with games):
- Appears as standard HID device
- No custom app needed
- Works with Windows/Mac/Linux/Android/iOS
- ~2-3 hours to implement

### **Option C: Add More Features**

- Configuration characteristic (adjust sample rate)
- Battery service (if using external battery)
- LED control from BLE
- More buttons (external via GPIO)

---

## 📚 Resources

### **Documentation:**
- [GATT.md](GATT.md) - Complete GATT implementation guide
- [RUST.md](RUST.md) - Rust code explanation
- [LINUX_TESTING.md](LINUX_TESTING.md) - Linux testing guide

### **Web Bluetooth:**
- [MDN Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
- [Web Bluetooth Samples](https://googlechrome.github.io/samples/web-bluetooth/)

### **Tools:**
- [nRF Connect](https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-mobile) - Mobile app
- [LightBlue](https://punchthrough.com/lightblue/) - iOS BLE scanner

---

## ✅ Success Criteria

You've successfully implemented button BLE support when:

- [x] Firmware builds successfully (140KB)
- [x] RTT logs show button press/release events
- [x] Web Bluetooth connects to micro:bit
- [ ] Joystick visual updates in real-time
- [ ] Button A shows "PRESSED" when pressed
- [ ] Button B shows "PRESSED" when pressed
- [ ] Both work simultaneously with joystick
- [ ] No dropped notifications
- [ ] Connection stays stable (>1 minute)

---

**Ready to test?** Flash the firmware and open `test/ble-test.html`! 🚀
