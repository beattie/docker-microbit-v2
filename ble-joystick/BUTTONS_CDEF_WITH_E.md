# All Four Buttons (C, D, E, F) Exercise - Using Button E Instead of Button A

Complete guide to adding all 4 Joystick:bit V2 buttons (C, D, E, F) by replacing micro:bit Button A with Joystick:bit Button E.

---

## ⚠️ Important Design Decision

**This guide chooses Joystick:bit Button E over micro:bit Button A**

### The Pin Conflict:
- **P14** is shared between:
  - micro:bit built-in Button A
  - Joystick:bit Button E

### Our Choice:
- ✅ Use **Joystick:bit Button E** (P14)
- ❌ Disable **micro:bit Button A**
- ✅ Keep **micro:bit Button B** (P23)
- ✅ Net result: **5 total buttons** (B + C, D, E, F)

**Rationale:** The Joystick:bit V2 is designed as a complete controller. Using all 4 Joystick:bit buttons provides a more cohesive gaming experience than mixing micro:bit and Joystick:bit buttons.

---

## 📋 Overview

**Hardware:** Joystick:bit V2 buttons C, D, E, F on **P12, P13, P14, P15**

**Features to Implement:**
- ✅ Read 4 Joystick:bit buttons (C, D, E, F)
- ✅ Keep micro:bit Button B for emergency/special use
- ✅ BLE GATT characteristics for all buttons
- ✅ Local feedback (buzzer + vibration)
- ✅ Edge detection for button events

**Button Layout:**
```
Joystick:bit V2:
[C] [D] [E] [F]  ← All on Joystick:bit board
 ↓   ↓   ↓   ↓
P12 P13 P14 P15

micro:bit:
[B] ← Kept for special functions
 ↓
P23
```

**Estimated Time:** 1-2 hours

---

## 🔧 Hardware Reference

### **Pin Mapping:**

| Button    | Pin  | nRF52833 Pin | Source      | Status    |
|-----------|------|--------------|-------------|-----------|
| B         | -    | P0_23        | micro:bit   | ✅ Active |
| C         | P12  | P0_12        | Joystick:bit| ✅ Active |
| D         | P13  | P0_13        | Joystick:bit| ✅ Active |
| E         | P14  | P0_14        | Joystick:bit| ✅ Active |
| F         | P15  | P0_15        | Joystick:bit| ✅ Active |
| ~~A~~     | ~~-~~| ~~P0_14~~    | ~~micro:bit~~| ❌ Disabled |

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
    button_a: u8, // 0 = released, 1 = pressed (micro:bit)
    button_b: u8, // 0 = released, 1 = pressed (micro:bit)
}
```

**Updated structure:**
```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,       // 0-1023 range, center at 512
    y: u16,       // 0-1023 range, center at 512
    button_b: u8, // 0 = released, 1 = pressed (micro:bit B - kept)
    button_c: u8, // 0 = released, 1 = pressed (Joystick:bit C)
    button_d: u8, // 0 = released, 1 = pressed (Joystick:bit D)
    button_e: u8, // 0 = released, 1 = pressed (Joystick:bit E - replaces A)
    button_f: u8, // 0 = released, 1 = pressed (Joystick:bit F)
}
```

**Why this approach:**
- Removes `button_a` (no longer needed)
- Adds `button_c`, `button_d`, `button_e`, `button_f`
- Keeps `button_b` for special functions
- Total: 5 buttons instead of 2

---

### **Step 2: Update BLE GATT Characteristics**

**Location:** `src/main.rs` in `JoystickService` struct

**Updated service:**
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,

    // REMOVED: button_a (was def3)

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,  // Kept - micro:bit Button B

    // NEW: All 4 Joystick:bit buttons
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef5", read, notify)]
    button_c: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef6", read, notify)]
    button_d: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef7", read, notify)]
    button_e: u8,  // Uses P14 (replaces micro:bit Button A)

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef8", read, notify)]
    button_f: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefa", write)]
    vibration_control: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefb", write)]
    buzzer_control: u8,
}
```

**UUID Allocation:**
```
Service: 12345678-1234-5678-1234-56789abcdef0

Read/Notify Characteristics:
def1 - X-Axis ✅
def2 - Y-Axis ✅
def3 - (unused - was Button A) ❌
def4 - Button B ✅ (micro:bit)
def5 - Button C ⭐ NEW (Joystick:bit)
def6 - Button D ⭐ NEW (Joystick:bit)
def7 - Button E ⭐ NEW (Joystick:bit - uses P14)
def8 - Button F ⭐ NEW (Joystick:bit)
def9 - (available)

Write Characteristics:
defa - Vibration ✅
defb - Buzzer ✅
defc-deff - (available)
```

---

### **Step 3: Update Joystick Read Task Signature**

**Location:** `src/main.rs` in `joystick_read_task()` function

**Updated signature:**
```rust
#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
    button_b: embassy_nrf::gpio::Input<'static>,      // micro:bit B (kept)
    button_c: embassy_nrf::gpio::Input<'static>,      // NEW: Joystick:bit C (P12)
    button_d: embassy_nrf::gpio::Input<'static>,      // NEW: Joystick:bit D (P13)
    button_e: embassy_nrf::gpio::Input<'static>,      // NEW: Joystick:bit E (P14)
    button_f: embassy_nrf::gpio::Input<'static>,      // NEW: Joystick:bit F (P15)
) {
```

**Note:** Removed `button_a` parameter entirely.

---

### **Step 4: Update Button State Tracking**

**Location:** Inside `joystick_read_task()`

**Update previous state tracking:**
```rust
    // Track previous button states for edge detection (haptic feedback)
    let mut btn_b_prev = false;  // micro:bit B
    let mut btn_c_prev = false;  // Joystick:bit C
    let mut btn_d_prev = false;  // Joystick:bit D
    let mut btn_e_prev = false;  // Joystick:bit E
    let mut btn_f_prev = false;  // Joystick:bit F
```

**Read all button states:**
```rust
        // Read button states (active-low: pressed = low = false)
        let btn_b_pressed = !button_b.is_high();  // micro:bit B
        let btn_c_pressed = !button_c.is_high();  // Joystick:bit C
        let btn_d_pressed = !button_d.is_high();  // Joystick:bit D
        let btn_e_pressed = !button_e.is_high();  // Joystick:bit E (P14)
        let btn_f_pressed = !button_f.is_high();  // Joystick:bit F
```

---

### **Step 5: Add Feedback for All Buttons**

**Location:** Inside `joystick_read_task()` loop

**Feedback section:**
```rust
        // Haptic + audio feedback on button press (rising edge detection)

        // micro:bit Button B - Special/emergency function (different feedback)
        if btn_b_pressed && !btn_b_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Double);
            BUZZER_SIGNAL.signal(BuzzerTone::Error);  // Special warning tone
            info!("  ⚠️  Feedback: Button B pressed (SPECIAL - double vibration + error tone)");
        }

        // Joystick:bit Button C
        if btn_c_pressed && !btn_c_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::C4);  // Low C
            info!("  🔊 Feedback: Button C pressed (vibration + C4)");
        }

        // Joystick:bit Button D
        if btn_d_pressed && !btn_d_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::D4);  // D
            info!("  🔊 Feedback: Button D pressed (vibration + D4)");
        }

        // Joystick:bit Button E (on P14 - replaced micro:bit A)
        if btn_e_pressed && !btn_e_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::E4);  // E
            info!("  🔊 Feedback: Button E pressed (vibration + E4)");
        }

        // Joystick:bit Button F
        if btn_f_pressed && !btn_f_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            BUZZER_SIGNAL.signal(BuzzerTone::A4);  // High A
            info!("  🔊 Feedback: Button F pressed (vibration + A4)");
        }

        // Update previous button states
        btn_b_prev = btn_b_pressed;
        btn_c_prev = btn_c_pressed;
        btn_d_prev = btn_d_pressed;
        btn_e_prev = btn_e_pressed;
        btn_f_prev = btn_f_pressed;
```

**Unique Tone Map:**
- Button B (micro:bit) → Error tone + Double vibration (special)
- Button C → C4 (262 Hz)
- Button D → D4 (294 Hz)
- Button E → E4 (330 Hz)
- Button F → A4 (440 Hz)

---

### **Step 6: Update JoystickData Signal**

**Location:** Inside `joystick_read_task()` loop

**Update the signal:**
```rust
        // Send joystick data to BLE task via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_b: btn_b_pressed as u8,  // micro:bit B
            button_c: btn_c_pressed as u8,  // Joystick:bit C
            button_d: btn_d_pressed as u8,  // Joystick:bit D
            button_e: btn_e_pressed as u8,  // Joystick:bit E
            button_f: btn_f_pressed as u8,  // Joystick:bit F
        };
        JOYSTICK_SIGNAL.signal(joystick_data);
```

---

### **Step 7: Update Logging**

**Location:** Inside `joystick_read_task()` loop

**Update info logging:**
```rust
            info!(
                "Joy {}: X={} (raw={} delta={} c={}), Y={} (raw={} delta={} c={}), B={} C={} D={} E={} F={}",
                count / 5,
                x_value,
                x_raw,
                x_delta,
                x_centered,
                y_value,
                y_raw,
                y_delta,
                y_centered,
                if btn_b_pressed { "1" } else { "0" },
                if btn_c_pressed { "1" } else { "0" },
                if btn_d_pressed { "1" } else { "0" },
                if btn_e_pressed { "1" } else { "0" },
                if btn_f_pressed { "1" } else { "0" },
            );
```

**Update button press logging:**
```rust
            // Log button press/release events
            if btn_b_pressed {
                info!("  🔘 Button B: PRESSED (micro:bit)");
            }
            if btn_c_pressed {
                info!("  🔘 Button C: PRESSED (Joystick:bit)");
            }
            if btn_d_pressed {
                info!("  🔘 Button D: PRESSED (Joystick:bit)");
            }
            if btn_e_pressed {
                info!("  🔘 Button E: PRESSED (Joystick:bit)");
            }
            if btn_f_pressed {
                info!("  🔘 Button F: PRESSED (Joystick:bit)");
            }
```

---

### **Step 8: Update BLE Connection Task**

**Location:** `src/main.rs` in `connection_task()`

**Update characteristic handles:**
```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_b_char = server.joystick_service.button_b;      // micro:bit B
    let btn_c_char = server.joystick_service.button_c;      // Joystick:bit C
    let btn_d_char = server.joystick_service.button_d;      // Joystick:bit D
    let btn_e_char = server.joystick_service.button_e;      // Joystick:bit E (P14)
    let btn_f_char = server.joystick_service.button_f;      // Joystick:bit F
    let vibration_char = server.joystick_service.vibration_control;
    let buzzer_char = server.joystick_service.buzzer_control;
```

**Initialize characteristics:**
```rust
    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_b_char.set(server, &0);
    let _ = btn_c_char.set(server, &0);
    let _ = btn_d_char.set(server, &0);
    let _ = btn_e_char.set(server, &0);
    let _ = btn_f_char.set(server, &0);
    let _ = vibration_char.set(server, &0);
    let _ = buzzer_char.set(server, &0);
```

**Update info message:**
```rust
    info!("[BLE] Starting notification loop (joystick + 5 buttons + vibration + buzzer)...");
```

**Update notifications:**
```rust
            embassy_futures::select::Either::Second(data) => {
                // Update characteristic values and notify
                let _ = x_char.set(server, &data.x);
                let _ = y_char.set(server, &data.y);
                let _ = btn_b_char.set(server, &data.button_b);
                let _ = btn_c_char.set(server, &data.button_c);
                let _ = btn_d_char.set(server, &data.button_d);
                let _ = btn_e_char.set(server, &data.button_e);
                let _ = btn_f_char.set(server, &data.button_f);

                let _ = x_char.notify(conn, &data.x).await;
                let _ = y_char.notify(conn, &data.y).await;
                let _ = btn_b_char.notify(conn, &data.button_b).await;
                let _ = btn_c_char.notify(conn, &data.button_c).await;
                let _ = btn_d_char.notify(conn, &data.button_d).await;
                let _ = btn_e_char.notify(conn, &data.button_e).await;
                let _ = btn_f_char.notify(conn, &data.button_f).await;
```

---

### **Step 9: Initialize GPIO Pins in Main**

**Location:** `src/main.rs` in `main()` function

**Update the joystick task spawn:**
```rust
    // Initialize Joystick:bit buttons (C, D, E, F)
    info!("Initializing Joystick:bit buttons (C, D, E, F)...");
    let button_c = embassy_nrf::gpio::Input::new(
        board.p12,
        embassy_nrf::gpio::Pull::Up,
    );
    let button_d = embassy_nrf::gpio::Input::new(
        board.p13,
        embassy_nrf::gpio::Pull::Up,
    );
    let button_e = embassy_nrf::gpio::Input::new(
        board.p14,  // ⚠️ This replaces micro:bit Button A
        embassy_nrf::gpio::Pull::Up,
    );
    let button_f = embassy_nrf::gpio::Input::new(
        board.p15,
        embassy_nrf::gpio::Pull::Up,
    );
    info!("✓ Joystick:bit buttons C, D, E, F initialized (active-low with pull-up)");
    info!("⚠️  Note: Button E uses P14 - micro:bit Button A is disabled");

    // Spawn joystick reading task
    info!("Spawning joystick task...");
    match spawner.spawn(joystick_read_task(
        board.saadc,
        board.p1,
        board.p2,
        board.btn_b,  // micro:bit Button B (kept)
        button_c,     // Joystick:bit C (P12)
        button_d,     // Joystick:bit D (P13)
        button_e,     // Joystick:bit E (P14) - replaces micro:bit A
        button_f,     // Joystick:bit F (P15)
    )) {
        Ok(_) => info!("✓ Joystick task spawned (5 buttons: B, C, D, E, F)"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }
```

**⚠️ Key Change:**
- Removed `board.btn_a` (no longer used)
- Added `board.p14` as `button_e` (Joystick:bit Button E)
- Kept `board.btn_b` (micro:bit Button B for special functions)

---

### **Step 10: Update GUI Test Script**

**Location:** `test/gui_test.py`

**Update UUIDs:**
```python
# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
# BTN_A_UUID removed - no longer used
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
BTN_C_UUID = "12345678-1234-5678-1234-56789abcdef5"
BTN_D_UUID = "12345678-1234-5678-1234-56789abcdef6"
BTN_E_UUID = "12345678-1234-5678-1234-56789abcdef7"  # Uses P14
BTN_F_UUID = "12345678-1234-5678-1234-56789abcdef8"
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"
BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"
```

**Update button display section:**
```python
        # Button indicators - micro:bit Button B
        mb_frame = tk.LabelFrame(
            self.root,
            text="micro:bit Button",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa'
        )
        mb_frame.pack(pady=10)

        self.btn_b_label = tk.Label(
            mb_frame,
            text="B: ○",
            font=("Arial", 24, "bold"),
            bg='#e74c3c',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_b_label.pack(padx=10, pady=10)

        # Button indicators - Joystick:bit Buttons C, D, E, F
        jb_frame = tk.LabelFrame(
            self.root,
            text="Joystick:bit Buttons",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa'
        )
        jb_frame.pack(pady=10)

        btn_row1 = tk.Frame(jb_frame, bg='#f8f9fa')
        btn_row1.pack(pady=5)
        btn_row2 = tk.Frame(jb_frame, bg='#f8f9fa')
        btn_row2.pack(pady=5)

        self.btn_c_label = tk.Label(
            btn_row1,
            text="C: ○",
            font=("Arial", 20, "bold"),
            bg='#3498db',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_c_label.pack(side=tk.LEFT, padx=8)

        self.btn_d_label = tk.Label(
            btn_row1,
            text="D: ○",
            font=("Arial", 20, "bold"),
            bg='#9b59b6',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_d_label.pack(side=tk.LEFT, padx=8)

        self.btn_e_label = tk.Label(
            btn_row2,
            text="E: ○",
            font=("Arial", 20, "bold"),
            bg='#27ae60',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_e_label.pack(side=tk.LEFT, padx=8)

        self.btn_f_label = tk.Label(
            btn_row2,
            text="F: ○",
            font=("Arial", 20, "bold"),
            bg='#e67e22',
            fg='white',
            width=4,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.btn_f_label.pack(side=tk.LEFT, padx=8)
```

**Add notification handlers:**
```python
            # Remove button A subscription
            # await self.client.start_notify(BTN_A_UUID, ...) - REMOVED

            # Subscribe to Button B (micro:bit)
            await self.client.start_notify(BTN_B_UUID, lambda _, data: self.handle_button_b(data))

            # Subscribe to Joystick:bit buttons C, D, E, F
            await self.client.start_notify(BTN_C_UUID, lambda _, data: self.handle_button_c(data))
            await self.client.start_notify(BTN_D_UUID, lambda _, data: self.handle_button_d(data))
            await self.client.start_notify(BTN_E_UUID, lambda _, data: self.handle_button_e(data))
            await self.client.start_notify(BTN_F_UUID, lambda _, data: self.handle_button_f(data))
```

**Update handler methods:**
```python
    def handle_button_b(self, data):
        """Handle Button B notification (micro:bit - special function)"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_b_label.config(text="B: ●", bg='#c0392b'))
        else:
            self.root.after(0, lambda: self.btn_b_label.config(text="B: ○", bg='#e74c3c'))

    def handle_button_c(self, data):
        """Handle Button C notification (Joystick:bit)"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_c_label.config(text="C: ●", bg='#2980b9'))
        else:
            self.root.after(0, lambda: self.btn_c_label.config(text="C: ○", bg='#3498db'))

    def handle_button_d(self, data):
        """Handle Button D notification (Joystick:bit)"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_d_label.config(text="D: ●", bg='#8e44ad'))
        else:
            self.root.after(0, lambda: self.btn_d_label.config(text="D: ○", bg='#9b59b6'))

    def handle_button_e(self, data):
        """Handle Button E notification (Joystick:bit - uses P14)"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_e_label.config(text="E: ●", bg='#229954'))
        else:
            self.root.after(0, lambda: self.btn_e_label.config(text="E: ○", bg='#27ae60'))

    def handle_button_f(self, data):
        """Handle Button F notification (Joystick:bit)"""
        value = int.from_bytes(data, byteorder='little')
        if value == 1:
            self.root.after(0, lambda: self.btn_f_label.config(text="F: ●", bg='#d35400'))
        else:
            self.root.after(0, lambda: self.btn_f_label.config(text="F: ○", bg='#e67e22'))
```

---

## 🧪 Testing

### **Test 1: Verify Pin Configuration**

**Expected RTT output:**
```
Initializing Joystick:bit buttons (C, D, E, F)...
✓ Joystick:bit buttons C, D, E, F initialized (active-low with pull-up)
⚠️  Note: Button E uses P14 - micro:bit Button A is disabled
Spawning joystick task...
✓ Joystick task spawned (5 buttons: B, C, D, E, F)
```

---

### **Test 2: Button Press Feedback**

Press each button and verify unique tones:

**micro:bit Button B (special):**
```
⚠️  Feedback: Button B pressed (SPECIAL - double vibration + error tone)
🔊 Buzzer tone: Error
🔊 Vibration pattern: Double
```

**Joystick:bit Button C:**
```
🔊 Feedback: Button C pressed (vibration + C4)
🔊 Buzzer tone: C4
```

**Joystick:bit Button D:**
```
🔊 Feedback: Button D pressed (vibration + D4)
🔊 Buzzer tone: D4
```

**Joystick:bit Button E (P14):**
```
🔊 Feedback: Button E pressed (vibration + E4)
🔊 Buzzer tone: E4
```

**Joystick:bit Button F:**
```
🔊 Feedback: Button F pressed (vibration + A4)
🔊 Buzzer tone: A4
```

---

### **Test 3: Musical Scale**

Press buttons in sequence to play a musical scale:

```
C → D → E → ... → A
C4  D4   E4      A4
262Hz → 294Hz → 330Hz → 440Hz
```

This creates a pleasing musical progression!

---

## 🎨 Creative Button Uses

### **Example 1: Gaming Controls**

```
Button B - Pause/Menu (special - double vibration alerts user)
Button C - Jump (low tone)
Button D - Duck (mid-low tone)
Button E - Attack (mid tone)
Button F - Special move (high tone)
```

### **Example 2: D-Pad Simulation**

```
Joystick - Movement
Button C - Action A
Button D - Action B
Button E - Action X
Button F - Action Y
Button B - Start/Select
```

### **Example 3: Musical Instrument**

Each button plays a different note:
```rust
if btn_c_pressed && !btn_c_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::C4);  // Do
}
if btn_d_pressed && !btn_d_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::D4);  // Re
}
if btn_e_pressed && !btn_e_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::E4);  // Mi
}
if btn_f_pressed && !btn_f_prev {
    BUZZER_SIGNAL.signal(BuzzerTone::A4);  // La
}
```

---

## ⚠️ Important Notes

### **Button A vs Button E Trade-off:**

**Lost:**
- ❌ micro:bit Button A (no longer accessible)
- ❌ Cannot use board.btn_a in code

**Gained:**
- ✅ All 4 Joystick:bit buttons (C, D, E, F)
- ✅ Cohesive controller layout
- ✅ Musical scale capability (C-D-E-F)
- ✅ Better gaming experience

### **Reverting Back:**

If you want micro:bit Button A back:
1. Change `board.p14` to `board.btn_a`
2. Remove Button E from the code
3. Use only C, D, F (3 Joystick:bit buttons)

---

## ✅ Success Criteria

- [ ] Firmware builds without errors
- [ ] RTT logs show "⚠️ Button E uses P14"
- [ ] micro:bit Button A does NOT respond
- [ ] Joystick:bit Button E (P14) works correctly
- [ ] All 5 buttons (B, C, D, E, F) work
- [ ] Each button has unique tone
- [ ] Musical scale works (C4→D4→E4→A4)
- [ ] GUI shows all 5 buttons

---

## 📚 Summary

### **Final Button Configuration:**

| Button | Pin  | Source       | Tone  | Vibration | Use        |
|--------|------|--------------|-------|-----------|------------|
| B      | P23  | micro:bit    | Error | Double    | Special    |
| C      | P12  | Joystick:bit | C4    | Short     | Normal     |
| D      | P13  | Joystick:bit | D4    | Short     | Normal     |
| E      | P14  | Joystick:bit | E4    | Short     | Normal     |
| F      | P15  | Joystick:bit | A4    | Short     | Normal     |

**Total: 5 buttons + Joystick = Complete controller!** 🎮

---

**Ready to use all 4 Joystick:bit buttons?** This configuration provides the best gaming experience! 🎵
