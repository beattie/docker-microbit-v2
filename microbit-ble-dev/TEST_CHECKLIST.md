# BLE Joystick Test Checklist

Print this or keep on your phone while testing!

---

## ⚙️ Pre-Flash Checklist

- [ ] micro:bit v2 connected via USB
- [ ] Joystick:bit properly seated on micro:bit
- [ ] Joystick wired to P1 (X-axis) and P2 (Y-axis)
- [ ] nRF Connect app installed on phone
- [ ] Phone Bluetooth enabled
- [ ] Project builds successfully

---

## 🔥 Flashing

```bash
cargo run --release
```

- [ ] Build completes without errors
- [ ] Programming shows progress bar
- [ ] "Finished" message appears

---

## 💡 Visual Indicators

### Startup Sequence (first 2 seconds):
- [ ] Top LED row blinks **3 times quickly**
- [ ] LEDs go off briefly

### Normal Operation:
- [ ] Top LED row blinks **slowly** (500ms on/off)
- [ ] Blinking continues indefinitely

**If LEDs don't blink:** Reset micro:bit (button on back)

---

## 📱 BLE Connection Test

### Phone Setup:
1. - [ ] Open nRF Connect app
2. - [ ] Tap "SCAN" button
3. - [ ] Look for **"microbit-joy"** in device list

### Connection:
4. - [ ] Tap "CONNECT" next to microbit-joy
5. - [ ] Status changes to "Connected"
6. - [ ] Services discovered automatically

**If not found:** Move closer, reset micro:bit, try again

---

## 🔍 Service Discovery

### Find Custom Service:
- [ ] Scroll to **"Unknown Service"**
- [ ] UUID shows: `12345678-1234-5678-1234-56789abcdef0`
- [ ] Tap to expand service

### Find Characteristics:
- [ ] See **2 characteristics** listed
- [ ] First: `...def1` (X-Axis)
- [ ] Second: `...def2` (Y-Axis)
- [ ] Both show "NOTIFY, READ" properties

---

## 📊 Enable Notifications

### X-Axis:
- [ ] Tap **↓** button on X-Axis characteristic
- [ ] Icon changes to **↓** with checkmark
- [ ] "Notifications enabled" message appears

### Y-Axis:
- [ ] Tap **↓** button on Y-Axis characteristic
- [ ] Icon changes to **↓** with checkmark
- [ ] "Notifications enabled" message appears

---

## 🕹️ Joystick Testing

### Center Position:
- [ ] Joystick at rest (centered)
- [ ] X-Axis reads approximately **512** (0x0200)
- [ ] Y-Axis reads approximately **512** (0x0200)
- [ ] Values are stable (±10)

### Movement Tests:

#### Test 1: Left Movement
- [ ] Move joystick fully **LEFT**
- [ ] X-Axis value **increases** (>900)
- [ ] Y-Axis stays around 512
- [ ] Release: X returns to ~512

#### Test 2: Right Movement
- [ ] Move joystick fully **RIGHT**
- [ ] X-Axis value **decreases** (<100)
- [ ] Y-Axis stays around 512
- [ ] Release: X returns to ~512

#### Test 3: Up Movement
- [ ] Move joystick fully **UP**
- [ ] Y-Axis value **increases** (>900)
- [ ] X-Axis stays around 512
- [ ] Release: Y returns to ~512

#### Test 4: Down Movement
- [ ] Move joystick fully **DOWN**
- [ ] Y-Axis value **decreases** (<100)
- [ ] X-Axis stays around 512
- [ ] Release: Y returns to ~512

#### Test 5: Diagonal Movement
- [ ] Move joystick to **TOP-LEFT**
- [ ] Both X and Y values **increase**
- [ ] Move to **BOTTOM-RIGHT**
- [ ] Both X and Y values **decrease**

### Update Rate:
- [ ] Values update **smoothly** as joystick moves
- [ ] No significant lag (<200ms)
- [ ] Notifications appear in real-time

---

## 🔄 Disconnect & Reconnect Test

### Disconnect:
- [ ] Tap "DISCONNECT" in app
- [ ] Connection closes cleanly
- [ ] micro:bit LEDs still blinking

### Reconnect:
- [ ] Tap "SCAN" again
- [ ] "microbit-joy" reappears in list
- [ ] Can reconnect successfully
- [ ] Services still work after reconnect

---

## 🐛 Troubleshooting Quick Checks

### Device Not Advertising:
```bash
# View logs
probe-rs run --chip nRF52833_xxAA target/thumbv7em-none-eabihf/release/ble-joystick
```
- [ ] See "[BLE] Advertising as 'microbit-joy'..." in logs
- [ ] No error messages in output

### Values Not Changing:
- [ ] Joystick is properly connected
- [ ] P1 connected to X-axis (check wiring)
- [ ] P2 connected to Y-axis (check wiring)
- [ ] Joystick has power (3.3V and GND)

### Calibration Off:
- [ ] Reset micro:bit
- [ ] **Don't touch joystick** during startup
- [ ] Wait for 3 quick LED blinks to complete
- [ ] Check center value again (~512)

---

## ✅ Success Criteria

All of these should be true:

- [x] Firmware flashes without errors
- [x] LEDs blink on startup and during operation
- [x] Device appears in BLE scan as "microbit-joy"
- [x] Can connect and discover services
- [x] Both characteristics support notifications
- [x] Notifications can be enabled
- [x] Center position reads ~512 on both axes
- [x] X-Axis changes when moving left/right
- [x] Y-Axis changes when moving up/down
- [x] Full range achievable (0-1023)
- [x] Values update in real-time (<200ms lag)
- [x] Can disconnect and reconnect

---

## 📈 Performance Check

### Update Rate:
- [ ] Move joystick continuously in circle
- [ ] Count notifications in 10 seconds
- [ ] Should receive ~100 updates (10Hz)

### Connection Stability:
- [ ] Keep connected for 1 minute
- [ ] Move joystick continuously
- [ ] No disconnections occur
- [ ] No notification errors

### Range Coverage:
| Position | Expected X | Expected Y | Actual X | Actual Y | ✓ |
|----------|-----------|-----------|----------|----------|---|
| Center | 512 | 512 | ____ | ____ | [ ] |
| Full Left | >900 | ~512 | ____ | ____ | [ ] |
| Full Right | <100 | ~512 | ____ | ____ | [ ] |
| Full Up | ~512 | >900 | ____ | ____ | [ ] |
| Full Down | ~512 | <100 | ____ | ____ | [ ] |

---

## 🎉 Completion

If all tests pass:

**CONGRATULATIONS!** 🎊

Your BLE joystick is fully functional!

### Next Steps:
1. Try the Web Bluetooth example in TESTING_GUIDE.md
2. Build a custom mobile app
3. Implement HID-over-GATT for game support
4. Add button press detection
5. Create a game that uses your joystick!

---

## 📋 Test Results

**Test Date:** _______________

**Tester:** _______________

**Hardware:**
- micro:bit v2 serial: _______________
- Joystick:bit model: _______________

**Software:**
- Firmware version: _______________
- nRF Connect version: _______________
- Phone model: _______________

**Overall Result:** [ ] PASS  [ ] FAIL

**Notes:**
________________________________________
________________________________________
________________________________________
________________________________________

---

**Need Help?** See TESTING_GUIDE.md for detailed troubleshooting.
