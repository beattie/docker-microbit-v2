# Additional Buttons (C, D, E, F) Exercise - BLE Support

Complete guide to adding the 4 additional Joystick:bit V2 buttons with BLE remote reading and local feedback.

---

## 📋 Overview

**Hardware:** Joystick:bit V2 buttons C, D, E, F on **P12, P13, P14, P15**

**Features to Implement:**
- ✅ Read 4 additional button states (C, D, E, F)
- ✅ BLE GATT characteristics for remote monitoring
- ✅ Local feedback (buzzer + vibration on press)
- ✅ Edge detection for button events
- ✅ Notification support for real-time updates

**Estimated Time:** 1-2 hours

**Difficulty:** Beginner-Intermediate (extends existing button code)

---

## 🎯 Learning Goals

By completing this exercise, you will learn:

1. **GPIO input configuration** for additional pins
2. **BLE GATT characteristics** for multiple inputs
3. **Scalable data structures** for multiple buttons
4. **Edge detection patterns** for event-driven feedback
5. **Code organization** for maintainable firmware

---

## 🔧 Hardware Reference

### **Joystick:bit V2 Button Specs:**
- **Button C:** P12 (nRF52833 pin P0_12)
- **Button D:** P13 (nRF52833 pin P0_13)
- **Button E:** P14 (nRF52833 pin P0_14) - *Note: conflicts with micro:bit Button A*
- **Button F:** P15 (nRF52833 pin P0_15)

**⚠️ Important:** P14 is used by micro:bit's Button A. You have two options:
1. **Skip Button E** - Use only C, D, F (recommended)
2. **Use Button E** - Disable micro:bit Button A (not recommended)

### **Electrical Characteristics:**
- **Type:** Tactile push buttons
- **Pull-up:** Internal (configured in code)
- **Logic:** Active-low (pressed = LOW, released = HIGH)
- **Debouncing:** Handled by sampling rate (10 Hz)

---

## 📝 Implementation Steps

### **Step 1: Update JoystickData Structure**

**Location:** `src/main.rs` (top of file)

**Current structure:**
```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,       // 0-1023 range, center at 512
    y: u16,       // 0-1023 range, center at 512
    button_a: u8, // 0 = released, 1 = pressed
    button_b: u8, // 0 = released, 1 = pressed
}
```

**Updated structure:**
```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,       // 0-1023 range, center at 512
    y: u16,       // 0-1023 range, center at 512
    button_a: u8, // 0 = released, 1 = pressed
    button_b: u8, // 0 = released, 1 = pressed
    button_c: u8, // NEW: 0 = released, 1 = pressed
    button_d: u8, // NEW: 0 = released, 1 = pressed
    button_f: u8, // NEW: 0 = released, 1 = pressed (skip E)
}
```

**Why this approach:**
- Keeps all button states together
- Single signal for all joystick data
- Backward compatible with existing code

---

### **Step 2: Add BLE GATT Characteristics**

**Location:** `src/main.rs` in `JoystickService` struct

**Current service:**
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    button_a: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefa", write)]
    vibration_control: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefb", write)]
    buzzer_control: u8,
}
```

**Updated service:**
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    button_a: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,

    // NEW: Additional buttons
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef5", read, notify)]
    button_c: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef6", read, notify)]
    button_d: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef7", read, notify)]
    button_f: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefa", write)]
    vibration_control: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefb", write)]
    buzzer_control: u8,
}
```

**UUID Allocation:**
```
Service: 12345678-1234-5678-1234-56789abcdef0

Characteristics (read/notify):
def1 - X-Axis ✅
def2 - Y-Axis ✅
def3 - Button A ✅
def4 - Button B ✅
def5 - Button C ⭐ NEW
def6 - Button D ⭐ NEW
def7 - Button F ⭐ NEW
def8 - (available)
def9 - (available)

Characteristics (write):
defa - Vibration ✅
defb - Buzzer ✅
defc-deff - (available)
```

---

### **Step 3: Update Joystick Read Task**

**Location:** `src/main.rs` in `joystick_read_task()` function signature

**Current signature:**
```rust
#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
    button_a: embassy_nrf::gpio::Input<'static>,
    button_b: embassy_nrf::gpio::Input<'static>,
) {
```

**Updated signature:**
```rust
#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
    button_a: embassy_nrf::gpio::Input<'static>,
    button_b: embassy_nrf::gpio::Input<'static>,
    button_c: embassy_nrf::gpio::Input<'static>,  // NEW
    button_d: embassy_nrf::gpio::Input<'static>,  // NEW
    button_f: embassy_nrf::gpio::Input<'static>,  // NEW
) {
```

**Inside the task - Add previous state tracking:**

Find this section:
```rust
    // Track previous button states for edge detection (haptic feedback)
    let mut btn_a_prev = false;
    let mut btn_b_prev = false;
```

Update to:
```rust
    // Track previous button states for edge detection (haptic feedback)
    let mut btn_a_prev = false;
    let mut btn_b_prev = false;
    let mut btn_c_prev = false;  // NEW
    let mut btn_d_prev = false;  // NEW
    let mut btn_f_prev = false;  // NEW
```

**Read additional button states:**

Find this section:
```rust
        // Read button states (active-low: pressed = low = false)
        let btn_a_pressed = !button_a.is_high();
        let btn_b_pressed = !button_b.is_high();
```

Update to:
```rust
        // Read button states (active-low: pressed = low = false)
        let btn_a_pressed = !button_a.is_high();
        let btn_b_pressed = !button_b.is_high();
        let btn_c_pressed = !button_c.is_high();  // NEW
        let btn_d_pressed = !button_d.is_high();  // NEW
        let btn_f_pressed = !button_f.is_high();  // NEW
```

**Add feedback for new buttons:**

Find this section:
```rust
        // Haptic feedback on button press (rising edge detection)
        if btn_a_pressed && !btn_a_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::C4);  // Low beep for button A
            info!("  🔊 Feedback: Button A pressed (vibration + beep)");
        }
        if btn_b_pressed && !btn_b_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::E4);  // Higher beep for button B
            info!("  🔊 Feedback: Button B pressed (vibration + beep)");
        }
```

Add after Button B:
```rust
        // NEW: Feedback for additional buttons
        if btn_c_pressed && !btn_c_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::G4);  // G4 for button C
            info!("  🔊 Feedback: Button C pressed (vibration + beep)");
        }
        if btn_d_pressed && !btn_d_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::A4);  // A4 for button D
            info!("  🔊 Feedback: Button D pressed (vibration + beep)");
        }
        if btn_f_pressed && !btn_f_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::Beep);  // Beep for button F
            info!("  🔊 Feedback: Button F pressed (vibration + beep)");
        }
```

**Update previous state tracking:**

Find:
```rust
        // Update previous button states
        btn_a_prev = btn_a_pressed;
        btn_b_prev = btn_b_pressed;
```

Update to:
```rust
        // Update previous button states
        btn_a_prev = btn_a_pressed;
        btn_b_prev = btn_b_pressed;
        btn_c_prev = btn_c_pressed;  // NEW
        btn_d_prev = btn_d_pressed;  // NEW
        btn_f_prev = btn_f_pressed;  // NEW
```

**Update JoystickData signal:**

Find:
```rust
        // Send joystick data to BLE task via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: btn_a_pressed as u8,
            button_b: btn_b_pressed as u8,
        };
        JOYSTICK_SIGNAL.signal(joystick_data);
```

Update to:
```rust
        // Send joystick data to BLE task via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: btn_a_pressed as u8,
            button_b: btn_b_pressed as u8,
            button_c: btn_c_pressed as u8,  // NEW
            button_d: btn_d_pressed as u8,  // NEW
            button_f: btn_f_pressed as u8,  // NEW
        };
        JOYSTICK_SIGNAL.signal(joystick_data);
```

**Update logging:**

Find:
```rust
            info!(
                "Joy {}: X={} (raw={} delta={} c={}), Y={} (raw={} delta={} c={}), Btn A={}, Btn B={}",
                count / 5,
                x_value,
                x_raw,
                x_delta,
                x_centered,
                y_value,
                y_raw,
                y_delta,
                y_centered,
                if btn_a_pressed { "PRESSED" } else { "released" },
                if btn_b_pressed { "PRESSED" } else { "released" }
            );
```

Update to:
```rust
            info!(
                "Joy {}: X={} (raw={} delta={} c={}), Y={} (raw={} delta={} c={}), A={}, B={}, C={}, D={}, F={}",
                count / 5,
                x_value,
                x_raw,
                x_delta,
                x_centered,
                y_value,
                y_raw,
                y_delta,
                y_centered,
                if btn_a_pressed { "1" } else { "0" },
                if btn_b_pressed { "1" } else { "0" },
                if btn_c_pressed { "1" } else { "0" },  // NEW
                if btn_d_pressed { "1" } else { "0" },  // NEW
                if btn_f_pressed { "1" } else { "0" },  // NEW
            );
```

And update button press logging:
```rust
            // Log button press/release events
            if btn_a_pressed {
                info!("  🔘 Button A: PRESSED");
            }
            if btn_b_pressed {
                info!("  🔘 Button B: PRESSED");
            }
            // NEW: Additional button logging
            if btn_c_pressed {
                info!("  🔘 Button C: PRESSED");
            }
            if btn_d_pressed {
                info!("  🔘 Button D: PRESSED");
            }
            if btn_f_pressed {
                info!("  🔘 Button F: PRESSED");
            }
```

---

### **Step 4: Update BLE Connection Task**

**Location:** `src/main.rs` in `connection_task()` function

**Add characteristic handles:**

Find:
```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let vibration_char = server.joystick_service.vibration_control;
    let buzzer_char = server.joystick_service.buzzer_control;
```

Update to:
```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let btn_c_char = server.joystick_service.button_c;  // NEW
    let btn_d_char = server.joystick_service.button_d;  // NEW
    let btn_f_char = server.joystick_service.button_f;  // NEW
    let vibration_char = server.joystick_service.vibration_control;
    let buzzer_char = server.joystick_service.buzzer_control;
```

**Initialize new characteristics:**

Find:
```rust
    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);
    let _ = btn_b_char.set(server, &0);
    let _ = vibration_char.set(server, &0);
    let _ = buzzer_char.set(server, &0);
```

Update to:
```rust
    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);
    let _ = btn_b_char.set(server, &0);
    let _ = btn_c_char.set(server, &0);  // NEW
    let _ = btn_d_char.set(server, &0);  // NEW
    let _ = btn_f_char.set(server, &0);  // NEW
    let _ = vibration_char.set(server, &0);
    let _ = buzzer_char.set(server, &0);
```

**Update notifications:**

Find:
```rust
            embassy_futures::select::Either::Second(data) => {
                // Update characteristic values and notify
                let _ = x_char.set(server, &data.x);
                let _ = y_char.set(server, &data.y);
                let _ = btn_a_char.set(server, &data.button_a);
                let _ = btn_b_char.set(server, &data.button_b);

                let _ = x_char.notify(conn, &data.x).await;
                let _ = y_char.notify(conn, &data.y).await;
                let _ = btn_a_char.notify(conn, &data.button_a).await;
                let _ = btn_b_char.notify(conn, &data.button_b).await;
```

Update to:
```rust
            embassy_futures::select::Either::Second(data) => {
                // Update characteristic values and notify
                let _ = x_char.set(server, &data.x);
                let _ = y_char.set(server, &data.y);
                let _ = btn_a_char.set(server, &data.button_a);
                let _ = btn_b_char.set(server, &data.button_b);
                let _ = btn_c_char.set(server, &data.button_c);  // NEW
                let _ = btn_d_char.set(server, &data.button_d);  // NEW
                let _ = btn_f_char.set(server, &data.button_f);  // NEW

                let _ = x_char.notify(conn, &data.x).await;
                let _ = y_char.notify(conn, &data.y).await;
                let _ = btn_a_char.notify(conn, &data.button_a).await;
                let _ = btn_b_char.notify(conn, &data.button_b).await;
                let _ = btn_c_char.notify(conn, &data.button_c).await;  // NEW
                let _ = btn_d_char.notify(conn, &data.button_d).await;  // NEW
                let _ = btn_f_char.notify(conn, &data.button_f).await;  // NEW
```

**Update info message:**

Find:
```rust
    info!("[BLE] Starting notification loop (joystick + buttons + vibration)...");
```

Update to:
```rust
    info!("[BLE] Starting notification loop (joystick + 5 buttons + vibration + buzzer)...");
```

---

### **Step 5: Initialize GPIO Pins in Main**

**Location:** `src/main.rs` in `main()` function

**Find the joystick task spawn:**
```rust
    // Spawn joystick reading task with ADC peripheral and pins
    info!("Spawning joystick task...");
    match spawner.spawn(joystick_read_task(board.saadc, board.p1, board.p2, board.btn_a, board.btn_b)) {
        Ok(_) => info!("✓ Joystick task spawned"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }
```

**Update to include new button pins:**

```rust
    // Initialize additional buttons (C, D, F) on Joystick:bit V2
    info!("Initializing additional buttons (C, D, F)...");
    let button_c = embassy_nrf::gpio::Input::new(
        board.p12,
        embassy_nrf::gpio::Pull::Up,
    );
    let button_d = embassy_nrf::gpio::Input::new(
        board.p13,
        embassy_nrf::gpio::Pull::Up,
    );
    let button_f = embassy_nrf::gpio::Input::new(
        board.p15,
        embassy_nrf::gpio::Pull::Up,
    );
    info!("✓ Buttons C, D, F initialized (active-low with pull-up)");

    // Spawn joystick reading task with ADC peripheral and pins
    info!("Spawning joystick task...");
    match spawner.spawn(joystick_read_task(
        board.saadc,
        board.p1,
        board.p2,
        board.btn_a,
        board.btn_b,
        button_c,  // NEW
        button_d,  // NEW
        button_f,  // NEW
    )) {
        Ok(_) => info!("✓ Joystick task spawned"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }
```

**⚠️ Note:** We're skipping Button E (P14) because it conflicts with micro:bit's Button A.

---

### **Step 6: Update GUI Test Script**

**Location:** `test/gui_test.py`

**Add new UUIDs:**
```python
# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
BTN_C_UUID = "12345678-1234-5678-1234-56789abcdef5"  # NEW
BTN_D_UUID = "12345678-1234-5678-1234-56789abcdef6"  # NEW
BTN_F_UUID = "12345678-1234-5678-1234-56789abcdef7"  # NEW
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"
BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"
```

**Add button displays to GUI:**

Find the button display section and add:
```python
        # Button C, D, F indicators
        btn_cdf_frame = tk.Frame(self.root, bg='#f8f9fa')
        btn_cdf_frame.pack(pady=10)

        self.btn_c_label = tk.Label(
            btn_cdf_frame,
            text="C: ○",
            font=("Arial", 24, "bold"),
            bg='#95a5a6',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_c_label.pack(side=tk.LEFT, padx=10)

        self.btn_d_label = tk.Label(
            btn_cdf_frame,
            text="D: ○",
            font=("Arial", 24, "bold"),
            bg='#95a5a6',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_d_label.pack(side=tk.LEFT, padx=10)

        self.btn_f_label = tk.Label(
            btn_cdf_frame,
            text="F: ○",
            font=("Arial", 24, "bold"),
            bg='#95a5a6',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_f_label.pack(side=tk.LEFT, padx=10)
```

**Add notification handlers:**

Find the notification handler setup and add:
```python
            # Subscribe to button C, D, F notifications
            await self.client.start_notify(BTN_C_UUID, lambda _, data: self.handle_button_c(data))
            await self.client.start_notify(BTN_D_UUID, lambda _, data: self.handle_button_d(data))
            await self.client.start_notify(BTN_F_UUID, lambda _, data: self.handle_button_f(data))
```

**Add handler methods:**
```python
    def handle_button_c(self, data):
        """Handle Button C notification"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_c_label.config(text="C: ●", bg='#3498db'))
        else:
            self.root.after(0, lambda: self.btn_c_label.config(text="C: ○", bg='#95a5a6'))

    def handle_button_d(self, data):
        """Handle Button D notification"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_d_label.config(text="D: ●", bg='#9b59b6'))
        else:
            self.root.after(0, lambda: self.btn_d_label.config(text="D: ○", bg='#95a5a6'))

    def handle_button_f(self, data):
        """Handle Button F notification"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_f_label.config(text="F: ●", bg='#e67e22'))
        else:
            self.root.after(0, lambda: self.btn_f_label.config(text="F: ○", bg='#95a5a6'))
```

**Update window size:**
```python
self.root.geometry("720x1500")  # Increased from 1400
self.root.minsize(720, 1500)
```

---

## 🧪 Testing

### **Test 1: Build and Flash**

```bash
# Build firmware
cargo build --release

# Flash to micro:bit
cargo run --release
```

**Expected RTT output:**
```
Initializing additional buttons (C, D, F)...
✓ Buttons C, D, F initialized (active-low with pull-up)
Spawning joystick task...
✓ Joystick task spawned
```

---

### **Test 2: Button Press Feedback**

**Press each button on Joystick:bit V2:**

**Button C:**
```
🔊 Feedback: Button C pressed (vibration + beep)
🔊 Buzzer tone: G4
🔊 Vibration pattern: Short
```

**Button D:**
```
🔊 Feedback: Button D pressed (vibration + beep)
🔊 Buzzer tone: A4
🔊 Vibration pattern: Short
```

**Button F:**
```
🔊 Feedback: Button F pressed (vibration + beep)
🔊 Buzzer tone: Beep
🔊 Vibration pattern: Short
```

---

### **Test 3: BLE Notifications**

```bash
# Run GUI test
python3 test/gui_test.py

# Steps:
1. Connect to micro:bit
2. Press buttons C, D, F on Joystick:bit
3. Verify button indicators change color
4. Check real-time updates
```

**Expected behavior:**
- Button C pressed → Blue indicator (●)
- Button D pressed → Purple indicator (●)
- Button F pressed → Orange indicator (●)
- Button released → Gray indicator (○)

---

### **Test 4: Python Test Script**

Create `test/test_buttons.py`:
```python
#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner

BTN_C_UUID = "12345678-1234-5678-1234-56789abcdef5"
BTN_D_UUID = "12345678-1234-5678-1234-56789abcdef6"
BTN_F_UUID = "12345678-1234-5678-1234-56789abcdef7"

async def test_buttons():
    device = await BleakScanner.find_device_by_name("microbit-joy", timeout=10.0)
    if not device:
        print("❌ micro:bit not found")
        return

    async with BleakClient(device) as client:
        print("✅ Connected!")

        def button_c_handler(sender, data):
            value = int.from_bytes(data, byteorder='little')
            print(f"Button C: {'PRESSED' if value == 1 else 'released'}")

        def button_d_handler(sender, data):
            value = int.from_bytes(data, byteorder='little')
            print(f"Button D: {'PRESSED' if value == 1 else 'released'}")

        def button_f_handler(sender, data):
            value = int.from_bytes(data, byteorder='little')
            print(f"Button F: {'PRESSED' if value == 1 else 'released'}")

        await client.start_notify(BTN_C_UUID, button_c_handler)
        await client.start_notify(BTN_D_UUID, button_d_handler)
        await client.start_notify(BTN_F_UUID, button_f_handler)

        print("\n📱 Press buttons C, D, F on Joystick:bit...")
        print("Press Ctrl+C to exit\n")

        await asyncio.sleep(60)

asyncio.run(test_buttons())
```

```bash
chmod +x test/test_buttons.py
python3 test/test_buttons.py
```

---

## 🐛 Troubleshooting

### **Issue: Button always reads as pressed**

**Cause:** Incorrect pull-up configuration or pin conflict

**Solution:**
```rust
// Verify pull-up is configured
let button_c = embassy_nrf::gpio::Input::new(
    board.p12,
    embassy_nrf::gpio::Pull::Up,  // Must have pull-up
);
```

---

### **Issue: Button E conflicts with micro:bit Button A**

**Cause:** P14 is shared between Joystick:bit Button E and micro:bit Button A

**Solutions:**

**Option 1: Skip Button E (recommended)**
```rust
// Only use buttons C, D, F
// Skip button E to avoid conflict
```

**Option 2: Disable micro:bit Button A**
```rust
// Remove board.btn_a from joystick_read_task parameters
// Use board.p14 for Button E instead
let button_e = embassy_nrf::gpio::Input::new(
    board.p14,
    embassy_nrf::gpio::Pull::Up,
);
```

---

### **Issue: No BLE notifications received**

**Check:**
1. Are characteristics initialized with 0?
2. Are notifications called in connection_task?
3. Is JoystickData updated with new fields?

**Debug:**
```rust
info!("Notifying button C: {}", data.button_c);
let _ = btn_c_char.notify(conn, &data.button_c).await;
```

---

## 📊 Performance Impact

### **Memory Usage:**
- **Additional RAM:** ~15 bytes (3 buttons × 5 bytes overhead)
- **Flash:** +2-3 KB (GPIO init + BLE characteristics)
- **Total:** Still well within limits

### **CPU Impact:**
- Button reading: Negligible (sampled at 10 Hz)
- BLE notifications: ~1-2% per button press
- Feedback (vibration + buzzer): ~5% during active feedback

---

## 🎨 Creative Extensions

### **1. Button Combinations**

Detect multiple button presses:
```rust
// Check for combos
if btn_c_pressed && btn_d_pressed {
    BUZZER_SIGNAL.signal(BuzzerTone::Success);
    info!("  🎮 Combo: C+D pressed!");
}
```

### **2. Unique Tones Per Button**

Different tone patterns for each button:
```rust
if btn_c_pressed && !btn_c_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::C4);  // Low
}
if btn_d_pressed && !btn_d_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::E4);  // Mid
}
if btn_f_pressed && !btn_f_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::A4);  // High
}
```

### **3. Button Mapping System**

Create configurable button actions:
```rust
enum ButtonAction {
    PlayTone(BuzzerTone),
    Vibrate(VibrationPattern),
    Both(BuzzerTone, VibrationPattern),
}

let button_c_action = ButtonAction::PlayTone(BuzzerTone::C4);
let button_d_action = ButtonAction::Both(BuzzerTone::Success, VibrationPattern::Double);
```

---

## ✅ Success Criteria

You've successfully implemented additional buttons when:

- [ ] Firmware builds without errors
- [ ] RTT logs show "✓ Buttons C, D, F initialized"
- [ ] Pressing buttons C, D, F triggers vibration + audio feedback
- [ ] GUI shows button state changes in real-time
- [ ] BLE notifications received for all buttons
- [ ] Each button has unique feedback tone
- [ ] No conflicts with existing functionality
- [ ] Binary size remains under 160 KB

---

## 🚀 Next Steps

### **Option A: Add Button E Support**
If you don't need micro:bit Button A, enable Button E:
```rust
// Replace board.btn_a with board.p14
```

### **Option B: Button Combinations**
Implement multi-button gesture detection

### **Option C: Button Remapping**
Create BLE characteristic to remap button functions dynamically

---

## 📚 Reference

### **Pin Mapping Summary:**

| Button | Pin  | nRF52833 Pin | Conflict? |
|--------|------|--------------|-----------|
| A      | -    | P0_14        | micro:bit |
| B      | -    | P0_23        | micro:bit |
| C      | P12  | P0_12        | ✅ None   |
| D      | P13  | P0_13        | ✅ None   |
| E      | P14  | P0_14        | ⚠️ Button A |
| F      | P15  | P0_15        | ✅ None   |

### **UUID Allocation:**

```
Service: 12345678-1234-5678-1234-56789abcdef0

Read/Notify:
def1 - X-Axis
def2 - Y-Axis
def3 - Button A
def4 - Button B
def5 - Button C ⭐
def6 - Button D ⭐
def7 - Button F ⭐

Write:
defa - Vibration
defb - Buzzer
```

---

**Ready to add more buttons?** Follow the steps above and expand your micro:bit controller! 🎮
