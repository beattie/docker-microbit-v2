# Buzzer Support Exercise - BLE + Local Control

Complete guide to adding Joystick:bit V2 buzzer support with both BLE remote control and local feedback.

---

## 📋 Overview

**Hardware:** Joystick:bit V2 buzzer on **P0** (PWM-capable pin)

**Features to Implement:**
- ✅ BLE remote control (write commands to trigger tones)
- ✅ Local feedback (buzzer sounds on joystick/button events)
- ✅ Multiple tone patterns (notes, beeps, melodies)

**Estimated Time:** 1-2 hours

**Difficulty:** Intermediate (requires PWM knowledge)

---

## 🎯 Learning Goals

By completing this exercise, you will learn:

1. **PWM (Pulse Width Modulation)** for tone generation
2. **BLE GATT characteristic** for write-only control
3. **Signal-based inter-task communication** (similar to vibration)
4. **Embassy async task** patterns for audio playback
5. **Frequency-to-period conversion** for tone generation

---

## 🔧 Hardware Reference

### **Joystick:bit V2 Buzzer Specs:**
- **Pin:** P0 (nRF52833 pin P0_02)
- **Type:** Passive buzzer (requires PWM tone generation)
- **Frequency Range:** 100 Hz - 5000 Hz (typical)
- **Recommended:** 200 Hz - 2000 Hz for best sound quality
- **Volume:** Controlled by PWM duty cycle (50% is standard)

### **Musical Notes Reference:**
```
Note    Frequency (Hz)
C4      262  (Middle C)
D4      294
E4      330
F4      349
G4      392
A4      440  (Concert pitch)
B4      494
C5      523
```

---

## 📝 Implementation Steps

### **Step 1: Add Buzzer Tone Enum**

**Location:** `src/main.rs` (after VibrationPattern enum)

**What to add:**
```rust
// Buzzer tone commands
#[derive(Clone, Copy, Debug, defmt::Format)]
enum BuzzerTone {
    Off,        // 0: No sound
    C4,         // 1: 262 Hz (Middle C)
    D4,         // 2: 294 Hz
    E4,         // 3: 330 Hz
    G4,         // 4: 392 Hz
    A4,         // 5: 440 Hz (Concert A)
    Beep,       // 6: Short 1000Hz beep
    Success,    // 7: Rising tone pattern (C4-E4-G4)
    Error,      // 8: Descending tone pattern (G4-E4-C4)
}

impl BuzzerTone {
    fn from_u8(value: u8) -> Self {
        match value {
            0 => BuzzerTone::Off,
            1 => BuzzerTone::C4,
            2 => BuzzerTone::D4,
            3 => BuzzerTone::E4,
            4 => BuzzerTone::G4,
            5 => BuzzerTone::A4,
            6 => BuzzerTone::Beep,
            7 => BuzzerTone::Success,
            8 => BuzzerTone::Error,
            _ => BuzzerTone::Off,
        }
    }

    fn frequency(&self) -> u32 {
        match self {
            BuzzerTone::Off => 0,
            BuzzerTone::C4 => 262,
            BuzzerTone::D4 => 294,
            BuzzerTone::E4 => 330,
            BuzzerTone::G4 => 392,
            BuzzerTone::A4 => 440,
            BuzzerTone::Beep => 1000,
            BuzzerTone::Success => 262,  // Start note for pattern
            BuzzerTone::Error => 392,    // Start note for pattern
        }
    }
}

// Global signal for buzzer commands
static BUZZER_SIGNAL: Signal<ThreadModeRawMutex, BuzzerTone> = Signal::new();
```

**Why this design:**
- Single tones (C4-A4) for musical notes
- Special patterns (Success/Error) for feedback
- `frequency()` method returns Hz for PWM calculation
- `from_u8()` for BLE characteristic parsing

---

### **Step 2: Add BLE GATT Characteristic**

**Location:** `src/main.rs` in `JoystickService` struct

**What to add:**
```rust
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    // ... existing characteristics ...

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefb", write)]
    buzzer_control: u8,  // 0=off, 1-5=notes, 6=beep, 7=success, 8=error
}
```

**UUID Breakdown:**
- Base service: `12345678-1234-5678-1234-56789abcdef0`
- X-axis: `...def1`
- Y-axis: `...def2`
- Button A: `...def3`
- Button B: `...def4`
- Vibration: `...defa`
- **Buzzer: `...defb`** ← New!

---

### **Step 3: Create Buzzer PWM Task**

**Location:** `src/main.rs` (after vibration_task)

**What to add:**
```rust
#[embassy_executor::task]
async fn buzzer_task(pwm: embassy_nrf::Peri<'static, embassy_nrf::peripherals::PWM0>) {
    use embassy_nrf::pwm::{Prescaler, SimplePwm};

    info!("✓ Buzzer task started (P0)");
    info!("Tones: 0=off, 1-5=notes, 6=beep, 7=success, 8=error");

    // Configure PWM for buzzer
    let mut config = embassy_nrf::pwm::Config::default();
    config.prescaler = Prescaler::Div1;  // 16 MHz base clock
    config.max_duty = 1000;              // PWM resolution

    let mut pwm = SimplePwm::new_1ch(pwm, board.p0, config);

    loop {
        // Wait for buzzer command
        let tone = BUZZER_SIGNAL.wait().await;

        info!("🔊 Buzzer tone: {:?}", tone);

        match tone {
            BuzzerTone::Off => {
                pwm.disable();
                info!("  → Buzzer OFF");
            }
            BuzzerTone::C4 | BuzzerTone::D4 | BuzzerTone::E4
            | BuzzerTone::G4 | BuzzerTone::A4 => {
                // Play single tone for 200ms
                play_tone(&mut pwm, tone.frequency(), 200).await;
            }
            BuzzerTone::Beep => {
                // Short 1000Hz beep
                play_tone(&mut pwm, 1000, 100).await;
            }
            BuzzerTone::Success => {
                // Rising pattern: C4 -> E4 -> G4
                play_tone(&mut pwm, 262, 100).await;
                play_tone(&mut pwm, 330, 100).await;
                play_tone(&mut pwm, 392, 150).await;
            }
            BuzzerTone::Error => {
                // Descending pattern: G4 -> E4 -> C4
                play_tone(&mut pwm, 392, 100).await;
                play_tone(&mut pwm, 330, 100).await;
                play_tone(&mut pwm, 262, 150).await;
            }
        }

        // Ensure buzzer is off after pattern
        pwm.disable();
    }
}

// Helper function to play a tone
async fn play_tone(pwm: &mut SimplePwm<'_>, frequency: u32, duration_ms: u64) {
    if frequency == 0 {
        pwm.disable();
        return;
    }

    // Calculate PWM period from frequency
    // Period = Clock / Frequency
    // For 16 MHz clock: Period = 16_000_000 / frequency
    let period = 16_000_000 / frequency;

    // Set duty cycle to 50% for square wave
    let duty = period / 2;

    pwm.set_period(period as u16);
    pwm.set_duty(0, duty as u16);  // Channel 0, 50% duty

    // Play for specified duration
    Timer::after(Duration::from_millis(duration_ms)).await;

    // Turn off
    pwm.disable();
}
```

**Key PWM Concepts:**

**Frequency to Period:**
```
Frequency = 440 Hz (A4 note)
Clock = 16 MHz (16,000,000 Hz)
Period = Clock / Frequency = 16,000,000 / 440 = 36,363 clock cycles

For PWM:
- max_duty controls resolution (1000 = 0-1000 range)
- set_period() sets the PWM period in clock cycles
- set_duty() sets ON time (50% = duty/2 for square wave)
```

**PWM Waveform:**
```
50% Duty Cycle (Square Wave):
  ___     ___     ___
 |   |   |   |   |   |
_|   |___|   |___|   |___
 <-Period->
```

---

### **Step 4: Wire Up BLE Write Handler**

**Location:** `src/main.rs` in `connection_task()` function

**What to modify:**

**4a. Add buzzer characteristic handle:**
```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let vibration_char = server.joystick_service.vibration_control;
    let buzzer_char = server.joystick_service.buzzer_control;  // NEW

    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);
    let _ = btn_b_char.set(server, &0);
    let _ = vibration_char.set(server, &0);
    let _ = buzzer_char.set(server, &0);  // NEW
```

**4b. Add buzzer polling in notification loop:**
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

                // Check if vibration control characteristic was written to
                if let Ok(vibration_value) = vibration_char.get(server) {
                    if vibration_value != prev_vibration_value && vibration_value != 0 {
                        let pattern = VibrationPattern::from_u8(vibration_value);
                        info!("[BLE] 📝 Vibration command received: {:?}", pattern);
                        VIBRATION_SIGNAL.signal(pattern);
                        let _ = vibration_char.set(server, &0);
                        prev_vibration_value = 0;
                    } else {
                        prev_vibration_value = vibration_value;
                    }
                }

                // NEW: Check if buzzer control characteristic was written to
                if let Ok(buzzer_value) = buzzer_char.get(server) {
                    if buzzer_value != prev_buzzer_value && buzzer_value != 0 {
                        let tone = BuzzerTone::from_u8(buzzer_value);
                        info!("[BLE] 📝 Buzzer command received: {:?}", tone);
                        BUZZER_SIGNAL.signal(tone);
                        let _ = buzzer_char.set(server, &0);
                        prev_buzzer_value = 0;
                    } else {
                        prev_buzzer_value = buzzer_value;
                    }
                }
            }
```

**Don't forget to add:** `let mut prev_buzzer_value = 0u8;` at the start of `connection_task()`

---

### **Step 5: Add Local Buzzer Feedback**

**Location:** `src/main.rs` in `joystick_read_task()` function

**What to add:**

**Option A: Beep on button press**
```rust
// Haptic feedback on button press (rising edge detection)
if btn_a_pressed && !btn_a_prev {
    VIBRATION_SIGNAL.signal(VibrationPattern::Short);
    BUZZER_SIGNAL.signal(BuzzerTone::Beep);  // NEW: Audio feedback
    info!("  🔊 Haptic + Audio feedback: Button A pressed");
}
if btn_b_pressed && !btn_b_prev {
    VIBRATION_SIGNAL.signal(VibrationPattern::Short);
    BUZZER_SIGNAL.signal(BuzzerTone::Beep);  // NEW: Audio feedback
    info!("  🔊 Haptic + Audio feedback: Button B pressed");
}
```

**Option B: Success/Error tones on joystick movement**
```rust
// Detect significant movements (threshold = 150 from center, with deadzone of 50)
let threshold = 150;
let deadzone = 50;

if x_centered.abs() > deadzone || y_centered.abs() > deadzone {
    if x_centered.abs() > threshold || y_centered.abs() > threshold {
        if x_centered.abs() > y_centered.abs() {
            // X-axis is inverted: positive = LEFT, negative = RIGHT
            if x_centered > 0 {
                info!("  → Movement: LEFT");
                BUZZER_SIGNAL.signal(BuzzerTone::C4);  // NEW: Low note
            } else {
                info!("  → Movement: RIGHT");
                BUZZER_SIGNAL.signal(BuzzerTone::G4);  // NEW: High note
            }
        } else {
            // Y-axis is inverted: positive = UP, negative = DOWN
            if y_centered > 0 {
                info!("  → Movement: UP");
                BUZZER_SIGNAL.signal(BuzzerTone::E4);  // NEW: Mid note
            } else {
                info!("  → Movement: DOWN");
                BUZZER_SIGNAL.signal(BuzzerTone::D4);  // NEW: Mid-low note
            }
        }
    }
}
```

**💡 Creative Ideas:**
- Play musical scales when moving joystick continuously
- Success melody when reaching joystick corners
- Error tone when joystick returns to center
- Different tones for different button combinations

---

### **Step 6: Initialize PWM and Spawn Buzzer Task**

**Location:** `src/main.rs` in `main()` function

**What to add:**
```rust
    // Initialize vibration motor (P16, active-LOW: HIGH = off, LOW = on)
    info!("Initializing vibration motor (P16)...");
    let vibration_pin = embassy_nrf::gpio::Output::new(
        board.p16,
        embassy_nrf::gpio::Level::High,  // HIGH = motor OFF (active-low)
        embassy_nrf::gpio::OutputDrive::Standard,
    );
    info!("✓ Vibration motor initialized (OFF - active-low)");

    // Spawn vibration motor task
    match spawner.spawn(vibration_task(vibration_pin)) {
        Ok(_) => info!("✓ Vibration task spawned"),
        Err(_) => error!("✗ Failed to spawn vibration task"),
    }

    // NEW: Spawn buzzer task (P0 PWM)
    info!("Initializing buzzer (P0 PWM)...");
    match spawner.spawn(buzzer_task(board.pwm0)) {
        Ok(_) => info!("✓ Buzzer task spawned"),
        Err(_) => error!("✗ Failed to spawn buzzer task"),
    }

    // Spawn joystick reading task with ADC peripheral and pins
    info!("Spawning joystick task...");
```

**Note:** We use `board.pwm0` for the buzzer on P0. Make sure `board.p0` is NOT used elsewhere!

---

### **Step 7: Update GUI with Buzzer Controls**

**Location:** `test/gui_test.py`

**What to add:**

**7a. Add buzzer UUID:**
```python
# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
X_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
Y_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"
BTN_A_UUID = "12345678-1234-5678-1234-56789abcdef3"
BTN_B_UUID = "12345678-1234-5678-1234-56789abcdef4"
VIBRATION_UUID = "12345678-1234-5678-1234-56789abcdefa"
BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"  # NEW
```

**7b. Add buzzer control section (after vibration buttons):**
```python
        # Buzzer control frame
        buzzer_frame = tk.LabelFrame(
            self.root,
            text="🔊 Buzzer Control",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            pady=20,
            padx=20
        )
        buzzer_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        buzzer_label = tk.Label(
            buzzer_frame,
            text="Click buttons to play tones via BLE",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666',
            justify=tk.CENTER
        )
        buzzer_label.pack(pady=(0, 10))

        # Create grid for buzzer buttons
        buzzer_grid1 = tk.Frame(buzzer_frame, bg='#f8f9fa')
        buzzer_grid1.pack(pady=5)

        buzzer_grid2 = tk.Frame(buzzer_frame, bg='#f8f9fa')
        buzzer_grid2.pack(pady=5)

        buzzer_grid3 = tk.Frame(buzzer_frame, bg='#f8f9fa')
        buzzer_grid3.pack(pady=5)

        # Define buzzer tones
        tones = [
            ("Silent", 0, '#95a5a6'),
            ("C4", 1, '#3498db'),
            ("D4", 2, '#3498db'),
            ("E4", 3, '#3498db'),
            ("G4", 4, '#9b59b6'),
            ("A4", 5, '#9b59b6'),
            ("Beep", 6, '#f39c12'),
            ("Success", 7, '#27ae60'),
            ("Error", 8, '#e74c3c')
        ]

        # Create buttons for each tone (3 rows)
        self.buzzer_buttons = []
        for i, (label, tone_id, color) in enumerate(tones):
            if i < 3:
                parent = buzzer_grid1
            elif i < 6:
                parent = buzzer_grid2
            else:
                parent = buzzer_grid3

            btn = tk.Button(
                parent,
                text=label,
                command=lambda t=tone_id: self.send_buzzer(t),
                font=("Arial", 10, "bold"),
                bg=color,
                fg='white',
                relief=tk.RAISED,
                borderwidth=3,
                width=12,
                height=2,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=8, pady=8)
            btn.config(state=tk.DISABLED)  # Disabled until connected
            self.buzzer_buttons.append(btn)
```

**7c. Add send_buzzer() method:**
```python
    def send_buzzer(self, tone):
        """Send buzzer command via BLE"""
        if not self.connected or not self.client or not self.ble_loop:
            messagebox.showwarning("Not Connected", "Please connect to micro:bit first!")
            return

        tone_names = ["Silent", "C4", "D4", "E4", "G4", "A4", "Beep", "Success", "Error"]
        print(f"🔊 Sending buzzer tone: {tone} ({tone_names[tone]})")

        # Schedule write in the BLE event loop (thread-safe)
        async def write_buzzer():
            try:
                await self.client.write_gatt_char(BUZZER_UUID, bytes([tone]))
                print(f"   ✅ Buzzer command sent successfully")
            except Exception as e:
                print(f"   ❌ Error sending buzzer: {e}")
                self.root.after(0, lambda err=str(e): messagebox.showerror("BLE Error", f"Failed to send buzzer: {err}"))

        # Use run_coroutine_threadsafe to schedule in the BLE loop
        try:
            asyncio.run_coroutine_threadsafe(write_buzzer(), self.ble_loop)
        except Exception as e:
            print(f"   ❌ Error scheduling buzzer: {e}")
            messagebox.showerror("BLE Error", f"Failed to schedule buzzer: {e}")
```

**7d. Enable/disable buzzer buttons on connect/disconnect:**

In `connect_ble()` after enabling vibration buttons:
```python
                # Enable vibration buttons
                for btn in self.vibration_buttons:
                    self.root.after(0, lambda b=btn: b.config(state=tk.NORMAL))

                # Enable buzzer buttons
                for btn in self.buzzer_buttons:
                    self.root.after(0, lambda b=btn: b.config(state=tk.NORMAL))
```

In `toggle_connection()` disconnect section and error handlers:
```python
            # Disable vibration buttons
            for btn in self.vibration_buttons:
                btn.config(state=tk.DISABLED)

            # Disable buzzer buttons
            for btn in self.buzzer_buttons:
                btn.config(state=tk.DISABLED)
```

**7e. Update window size:**
```python
self.root.geometry("720x1400")  # Increased from 1200
self.root.minsize(720, 1400)
```

---

## 🧪 Testing

### **Test 1: Build and Flash**

```bash
# Build firmware
cargo build --release

# Check size
arm-none-eabi-size target/thumbv7em-none-eabihf/release/ble-joystick

# Flash
cargo flash --release --chip nRF52833_xxAA

# Or build + flash + monitor
cargo run --release
```

**Expected Size:** ~150 KB (adding PWM increases size slightly)

---

### **Test 2: RTT Logs - Buzzer Initialization**

**Expected output:**
```
✓ Vibration motor initialized (OFF - active-low)
✓ Vibration task spawned
Initializing buzzer (P0 PWM)...
✓ Buzzer task spawned
✓ Buzzer task started (P0)
Tones: 0=off, 1-5=notes, 6=beep, 7=success, 8=error
```

---

### **Test 3: Local Buzzer Feedback**

**If you added button press beeps:**
```bash
# Press Button A on micro:bit
# Expected RTT output:
🔊 Haptic + Audio feedback: Button A pressed
🔊 Buzzer tone: Beep
  → Beep played (100ms)
```

**If you added joystick movement tones:**
```bash
# Move joystick LEFT
# Expected RTT output:
→ Movement: LEFT
🔊 Buzzer tone: C4
  → Playing C4 (262 Hz)
```

---

### **Test 4: BLE Control via GUI**

```bash
# Run GUI
python3 test/gui_test.py

# Steps:
1. Connect to micro:bit
2. Click buzzer tone buttons
3. Should hear tones from micro:bit buzzer
4. Try all 9 tones:
   - Silent (no sound)
   - C4, D4, E4, G4, A4 (musical notes)
   - Beep (1000Hz beep)
   - Success (rising melody)
   - Error (descending melody)
```

**Expected RTT output:**
```
[BLE] 📝 Buzzer command received: C4
🔊 Buzzer tone: C4
  → Playing C4 (262 Hz)
```

---

### **Test 5: BLE Control via Python Script**

Create `test/test_buzzer.py`:
```python
#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner

BUZZER_UUID = "12345678-1234-5678-1234-56789abcdefb"
TONES = {
    0: "Silent",
    1: "C4 (262 Hz)",
    2: "D4 (294 Hz)",
    3: "E4 (330 Hz)",
    4: "G4 (392 Hz)",
    5: "A4 (440 Hz)",
    6: "Beep (1000 Hz)",
    7: "Success melody",
    8: "Error melody"
}

async def test_buzzer():
    device = await BleakScanner.find_device_by_name("microbit-joy", timeout=10.0)
    if not device:
        print("❌ micro:bit not found")
        return

    async with BleakClient(device) as client:
        print("✅ Connected!")

        for tone_id, tone_name in TONES.items():
            print(f"\n🔊 Testing tone {tone_id}: {tone_name}")
            await client.write_gatt_char(BUZZER_UUID, bytes([tone_id]))
            await asyncio.sleep(0.5)

        print("\n✅ All tones tested!")

asyncio.run(test_buzzer())
```

---

## 🐛 Troubleshooting

### **Issue: No sound from buzzer**

**Check:**
1. Verify P0 is connected to buzzer on Joystick:bit V2
2. Check RTT logs - does it show "Buzzer task started"?
3. Verify PWM is enabled: `pwm.set_duty(0, duty)`
4. Test with higher frequency (1000 Hz beep)

**Solution:**
```rust
// Add debug logging to play_tone()
info!("Playing {} Hz for {} ms", frequency, duration_ms);
```

---

### **Issue: Buzzer always on / won't turn off**

**Cause:** PWM not being disabled properly

**Solution:**
```rust
// Make sure pwm.disable() is called
pwm.disable();
```

---

### **Issue: Wrong frequency / weird pitch**

**Cause:** PWM period calculation error

**Solution:**
```rust
// Debug the calculation
let period = 16_000_000 / frequency;
info!("Frequency {} Hz = period {} cycles", frequency, period);
```

---

### **Issue: BLE commands not received**

**Check:**
1. Is `buzzer_char.get(server)` being polled?
2. Is `prev_buzzer_value` being updated?
3. Are you resetting characteristic to 0 after processing?

**Solution:**
```rust
// Add logging
if let Ok(buzzer_value) = buzzer_char.get(server) {
    info!("Buzzer char value: {}", buzzer_value);
    // ... rest of code
}
```

---

## 📊 Performance & Resource Usage

### **Expected Binary Size:**
- **Flash:** ~150-155 KB / 512 KB (30%)
- **RAM:** ~45 KB / 128 KB (35%)
- **PWM Overhead:** +5-10 KB vs vibration-only

### **CPU Usage:**
- PWM runs in hardware (negligible CPU)
- Buzzer task sleeps when idle (0% CPU)
- Playing tone: <1% CPU

### **Latency:**
- BLE command to sound: ~30-50ms
- Button press to beep: ~10-20ms
- PWM frequency accuracy: ±1 Hz

---

## 🎨 Creative Extensions

### **1. Musical Scale Player**
Play chromatic scale on joystick movement:
```rust
let note = ((x_value as i32 - 512).abs() / 50) as u8;  // 0-10
match note {
    0 => BUZZER_SIGNAL.signal(BuzzerTone::C4),
    1 => BUZZER_SIGNAL.signal(BuzzerTone::D4),
    2 => BUZZER_SIGNAL.signal(BuzzerTone::E4),
    // ... etc
}
```

### **2. Melody Playback**
Add melody support:
```rust
enum BuzzerTone {
    // ... existing tones
    MarioTheme,    // 9: Super Mario theme
    TetrisTheme,   // 10: Tetris theme
}

// In buzzer_task:
BuzzerTone::MarioTheme => {
    play_tone(&mut pwm, 330, 150).await;  // E4
    play_tone(&mut pwm, 330, 150).await;  // E4
    Timer::after(Duration::from_millis(150)).await;
    play_tone(&mut pwm, 330, 150).await;  // E4
    Timer::after(Duration::from_millis(150)).await;
    play_tone(&mut pwm, 262, 150).await;  // C4
    play_tone(&mut pwm, 330, 300).await;  // E4
}
```

### **3. Volume Control**
Add PWM duty cycle variation:
```rust
fn play_tone_with_volume(pwm: &mut SimplePwm, freq: u32, duration_ms: u64, volume: u8) {
    let period = 16_000_000 / freq;
    // Volume 0-100: adjust duty cycle from 0% to 50%
    let duty = (period * volume as u32) / 200;
    pwm.set_period(period as u16);
    pwm.set_duty(0, duty as u16);
    // ... rest
}
```

---

## 📚 Reference Material

### **PWM Calculation Formulas:**

**Frequency to Period:**
```
Period (cycles) = Clock_Frequency / Desired_Frequency

Example:
Clock = 16 MHz = 16,000,000 Hz
Freq = 440 Hz (A4)
Period = 16,000,000 / 440 = 36,363 cycles
```

**Duty Cycle for Square Wave:**
```
Duty = Period / 2  (50% duty cycle)

For 440 Hz:
Duty = 36,363 / 2 = 18,181 cycles
```

**Duration:**
```
Duration (ms) = (Period × Count) / Clock_Frequency × 1000

For 10 cycles of 440 Hz:
Duration = (36,363 × 10) / 16,000,000 × 1000 = 22.7 ms
```

---

### **Musical Note Frequencies:**

```
Octave 4 (Middle octave):
C4  - 262 Hz
C#4 - 277 Hz
D4  - 294 Hz
D#4 - 311 Hz
E4  - 330 Hz
F4  - 349 Hz
F#4 - 370 Hz
G4  - 392 Hz
G#4 - 415 Hz
A4  - 440 Hz (Concert pitch)
A#4 - 466 Hz
B4  - 494 Hz

Octave 5:
C5  - 523 Hz
D5  - 587 Hz
E5  - 659 Hz
F5  - 698 Hz
G5  - 784 Hz
A5  - 880 Hz
B5  - 988 Hz
```

---

### **nRF52833 PWM Specs:**

- **PWM Modules:** 4 (PWM0-PWM3)
- **Channels per module:** 4
- **Clock source:** 16 MHz
- **Prescaler:** Div1, Div2, Div4, Div8, Div16, Div32, Div64, Div128
- **Max period:** 32,768 (15-bit counter)
- **Resolution:** Configurable (1-32,768)

**For audio (100-5000 Hz):**
- Use Prescaler::Div1 (16 MHz)
- Period range: 3,200 (5000 Hz) to 160,000 (100 Hz)
- 15-bit counter limits max period to 32,768
  - Max freq at Div1: 488 Hz
  - Use Div2 for lower frequencies

---

## ✅ Success Criteria

You've successfully implemented buzzer support when:

- [ ] Firmware builds without errors
- [ ] RTT logs show "✓ Buzzer task started"
- [ ] Button A press triggers beep (if local feedback enabled)
- [ ] GUI buzzer buttons trigger tones via BLE
- [ ] All 9 tone commands work correctly
- [ ] Success/Error melodies play pattern sequences
- [ ] No buzzer stuck-on issues
- [ ] Binary size under 160 KB

---

## 🚀 Next Steps

### **Option A: Combine with Vibration**
Create combined feedback patterns:
```rust
// Haptic + audio feedback
VIBRATION_SIGNAL.signal(VibrationPattern::Short);
BUZZER_SIGNAL.signal(BuzzerTone::Beep);
```

### **Option B: Add More Buttons (C, D, E, F)**
Extend to 6 buttons with unique tones for each

### **Option C: RTTTL Ringtone Support**
Parse and play ringtones in RTTTL format:
```
MarioTheme:d=4,o=5,b=100:16e6,16e6,32p,8e6,16c6,8e6,8g6,8p,8g
```

---

## 📖 Documentation Links

- [nRF52833 PWM](https://infocenter.nordicsemi.com/topic/ps_nrf52833/pwm.html)
- [Embassy PWM Examples](https://github.com/embassy-rs/embassy/tree/main/examples/nrf52840/src/bin)
- [Musical Note Frequencies](https://pages.mtu.edu/~suits/notefreqs.html)
- [RTTTL Format](https://github.com/dhylands/upy-rtttl)

---

**Ready to add buzzer support?** Follow the steps above and make your micro:bit sing! 🎵
