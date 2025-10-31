# Joystick:bit V2 Expansion Guide

Guide to expanding the BLE joystick firmware to support all Joystick:bit V2 features.

---

## Current Implementation

✅ **Joystick X-axis** (P1) - READ + NOTIFY
✅ **Joystick Y-axis** (P2) - READ + NOTIFY
✅ **Button A** (Built-in) - READ + NOTIFY
✅ **Button B** (Built-in) - READ + NOTIFY

**Binary Size:** 140 KB / 512 KB (27% flash)

---

## Available Expansions

### 1. Four Additional Buttons (C, D, E, F)
### 2. Buzzer Support (P0)
### 3. Vibration Motor (P16)

---

## Option 1: Add Buttons C, D, E, F

Add 4 more buttons from the Joystick:bit V2 board to create a **6-button gamepad**.

### Hardware Pins

| Button | micro:bit Pin | GPIO |
|--------|---------------|------|
| C | P12 | P0_02 |
| D | P13 | P0_01 |
| E | P14 | P0_00 |
| F | P15 | P0_24 |

### Implementation Steps

#### Step 1: Update JoystickData Structure

```rust
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,       // 0-1023 range, center at 512
    y: u16,       // 0-1023 range, center at 512
    button_a: u8, // 0 = released, 1 = pressed
    button_b: u8, // 0 = released, 1 = pressed
    button_c: u8, // NEW: 0 = released, 1 = pressed
    button_d: u8, // NEW: 0 = released, 1 = pressed
    button_e: u8, // NEW: 0 = released, 1 = pressed
    button_f: u8, // NEW: 0 = released, 1 = pressed
}
```

#### Step 2: Add BLE Characteristics

```rust
// Custom Joystick Service with 6 Buttons
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

    // NEW: Four additional buttons
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef5", read, notify)]
    button_c: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef6", read, notify)]
    button_d: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef7", read, notify)]
    button_e: u8,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef8", read, notify)]
    button_f: u8,
}
```

#### Step 3: Initialize GPIO Pins

⚠️ **Need to determine button configuration:**
- Are they active-low with pull-up? (like A/B)
- Are they active-high with pull-down?

**Test first with simple program:**

```rust
use embassy_nrf::gpio::{Input, Pull};

// In main():
let btn_c = Input::new(board.p12, Pull::Up);  // Test with Pull::Up first
let btn_d = Input::new(board.p13, Pull::Up);
let btn_e = Input::new(board.p14, Pull::Up);
let btn_f = Input::new(board.p15, Pull::Up);

// If buttons read opposite, try Pull::Down
```

#### Step 4: Update joystick_read_task

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
    button_e: embassy_nrf::gpio::Input<'static>,  // NEW
    button_f: embassy_nrf::gpio::Input<'static>,  // NEW
) {
    // ... existing ADC setup ...

    loop {
        // ... existing joystick reading ...

        // Read all 6 button states
        let btn_a_pressed = !button_a.is_high();
        let btn_b_pressed = !button_b.is_high();
        let btn_c_pressed = !button_c.is_high();  // NEW (adjust if active-high)
        let btn_d_pressed = !button_d.is_high();  // NEW
        let btn_e_pressed = !button_e.is_high();  // NEW
        let btn_f_pressed = !button_f.is_high();  // NEW

        // Send data via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: btn_a_pressed as u8,
            button_b: btn_b_pressed as u8,
            button_c: btn_c_pressed as u8,  // NEW
            button_d: btn_d_pressed as u8,  // NEW
            button_e: btn_e_pressed as u8,  // NEW
            button_f: btn_f_pressed as u8,  // NEW
        };
        JOYSTICK_SIGNAL.signal(joystick_data);

        // ... logging ...
    }
}
```

#### Step 5: Update connection_task

```rust
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let btn_c_char = server.joystick_service.button_c;  // NEW
    let btn_d_char = server.joystick_service.button_d;  // NEW
    let btn_e_char = server.joystick_service.button_e;  // NEW
    let btn_f_char = server.joystick_service.button_f;  // NEW

    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);
    let _ = btn_b_char.set(server, &0);
    let _ = btn_c_char.set(server, &0);  // NEW
    let _ = btn_d_char.set(server, &0);  // NEW
    let _ = btn_e_char.set(server, &0);  // NEW
    let _ = btn_f_char.set(server, &0);  // NEW

    loop {
        // ... existing select logic ...

        embassy_futures::select::Either::Second(data) => {
            // Update and notify all characteristics
            let _ = x_char.set(server, &data.x);
            let _ = y_char.set(server, &data.y);
            let _ = btn_a_char.set(server, &data.button_a);
            let _ = btn_b_char.set(server, &data.button_b);
            let _ = btn_c_char.set(server, &data.button_c);  // NEW
            let _ = btn_d_char.set(server, &data.button_d);  // NEW
            let _ = btn_e_char.set(server, &data.button_e);  // NEW
            let _ = btn_f_char.set(server, &data.button_f);  // NEW

            let _ = x_char.notify(conn, &data.x).await;
            let _ = y_char.notify(conn, &data.y).await;
            let _ = btn_a_char.notify(conn, &data.button_a).await;
            let _ = btn_b_char.notify(conn, &data.button_b).await;
            let _ = btn_c_char.notify(conn, &data.button_c).await;  // NEW
            let _ = btn_d_char.notify(conn, &data.button_d).await;  // NEW
            let _ = btn_e_char.notify(conn, &data.button_e).await;  // NEW
            let _ = btn_f_char.notify(conn, &data.button_f).await;  // NEW
        }
    }
}
```

#### Step 6: Update main()

```rust
#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let board = Microbit::new(Config::default());

    // Initialize additional button pins
    let btn_c = Input::new(board.p12, Pull::Up);
    let btn_d = Input::new(board.p13, Pull::Up);
    let btn_e = Input::new(board.p14, Pull::Up);
    let btn_f = Input::new(board.p15, Pull::Up);

    // Spawn joystick task with all 6 buttons
    match spawner.spawn(joystick_read_task(
        board.saadc,
        board.p1,
        board.p2,
        board.btn_a,
        board.btn_b,
        btn_c,  // NEW
        btn_d,  // NEW
        btn_e,  // NEW
        btn_f,  // NEW
    )) {
        Ok(_) => info!("✓ Joystick task spawned (6 buttons)"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }

    // ... rest of BLE initialization ...
}
```

### Estimated Impact

- **Binary Size:** +2-3 KB (143 KB total, still 28% flash)
- **RAM:** No significant change
- **Implementation Time:** 30-45 minutes
- **Difficulty:** ⭐⭐☆☆☆ (Easy, same pattern as A/B)

### Testing

1. **RTT Logs:** Verify all 6 buttons show press/release
2. **Web Bluetooth:** Update `test/ble-test.html` to show 6 buttons
3. **Python:** Update `test/test_buttons.py` to monitor all UUIDs

---

## Option 2: Buzzer Support (P0)

Add audio feedback capability using the onboard buzzer.

### Hardware

| Component | Pin | Type |
|-----------|-----|------|
| Buzzer | P0 | PWM Output |

### Implementation Approaches

#### Approach A: BLE-Controlled Buzzer

**Use case:** Remote control buzzer from client application

```rust
// Add to GATT service
#[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef9", write)]
buzzer_control: u8,  // 0-255: frequency/volume control
```

#### Approach B: Local Feedback

**Use case:** Buzzer beeps on button press (no BLE control)

```rust
use embassy_nrf::pwm::{Prescaler, SimplePwm};

#[embassy_executor::task]
async fn buzzer_task(pwm: embassy_nrf::Peri<'static, embassy_nrf::peripherals::PWM0>) {
    let mut pwm = SimplePwm::new_1ch(pwm, board.p0);

    loop {
        // Wait for button press signal
        // Play beep: 1000Hz for 100ms
        pwm.set_prescaler(Prescaler::Div16);
        pwm.set_max_duty(1000);
        pwm.set_duty(0, 500);  // 50% duty cycle
        Timer::after(Duration::from_millis(100)).await;
        pwm.set_duty(0, 0);  // Silent

        Timer::after(Duration::from_millis(100)).await;
    }
}
```

#### Approach C: Hybrid (BLE + Local)

**Use case:** BLE can trigger buzzer, buttons also trigger locally

```rust
// Signal for buzzer commands
static BUZZER_SIGNAL: Signal<ThreadModeRawMutex, BuzzerCommand> = Signal::new();

#[derive(Clone, Copy)]
enum BuzzerCommand {
    Beep { frequency: u16, duration_ms: u16 },
    ButtonPress,
    Silent,
}
```

### BLE Characteristic Options

```rust
// Option 1: Simple on/off
#[characteristic(uuid = "...def9", write)]
buzzer_enable: u8,  // 0 = off, 1 = on

// Option 2: Frequency control
#[characteristic(uuid = "...def9", write)]
buzzer_frequency: u16,  // Hz (100-5000)

// Option 3: Pattern control
#[characteristic(uuid = "...def9", write)]
buzzer_pattern: [u8; 8],  // Array of [freq, duration] pairs
```

### Estimated Impact

- **Binary Size:** +3-5 KB
- **Implementation Time:** 1-2 hours
- **Difficulty:** ⭐⭐⭐☆☆ (Medium, requires PWM knowledge)

### Use Cases

1. **Game audio feedback** - Beeps for actions/events
2. **Remote alarms** - Trigger buzzer from phone
3. **Button confirmation** - Audio feedback on button press
4. **Music/tones** - Play simple melodies

---

## Option 3: Vibration Motor (P16)

Add haptic feedback using the onboard vibration motor.

### Hardware

| Component | Pin | Type |
|-----------|-----|------|
| Vibration Motor | P16 | Digital Output (On/Off) |

### Implementation Approaches

#### Approach A: BLE-Controlled Vibration

```rust
// Add to GATT service
#[characteristic(uuid = "...defa", write)]
vibration_control: u8,  // 0 = off, 1 = on, 2-255 = pattern ID
```

#### Approach B: Automatic Button Feedback

**Use case:** Motor vibrates when any button is pressed

```rust
use embassy_nrf::gpio::Output;

#[embassy_executor::task]
async fn vibration_task(pin: embassy_nrf::gpio::Output<'static>) {
    loop {
        // Wait for button press signal
        let btn_pressed = BUTTON_PRESS_SIGNAL.wait().await;

        if btn_pressed {
            pin.set_high();  // Motor ON
            Timer::after(Duration::from_millis(50)).await;
            pin.set_low();   // Motor OFF
        }
    }
}
```

#### Approach C: Pattern-Based Vibration

**Use case:** Different vibration patterns for different events

```rust
static VIBRATION_SIGNAL: Signal<ThreadModeRawMutex, VibrationPattern> = Signal::new();

#[derive(Clone, Copy)]
enum VibrationPattern {
    Short,      // 50ms
    Medium,     // 150ms
    Long,       // 300ms
    Double,     // Two 50ms pulses
    Triple,     // Three 50ms pulses
}

#[embassy_executor::task]
async fn vibration_task(mut pin: embassy_nrf::gpio::Output<'static>) {
    loop {
        let pattern = VIBRATION_SIGNAL.wait().await;

        match pattern {
            VibrationPattern::Short => {
                pin.set_high();
                Timer::after(Duration::from_millis(50)).await;
                pin.set_low();
            }
            VibrationPattern::Double => {
                for _ in 0..2 {
                    pin.set_high();
                    Timer::after(Duration::from_millis(50)).await;
                    pin.set_low();
                    Timer::after(Duration::from_millis(50)).await;
                }
            }
            // ... other patterns ...
        }
    }
}
```

### Implementation Code

```rust
// In main():
let vibration_pin = Output::new(board.p16, Level::Low, OutputDrive::Standard);
spawner.spawn(vibration_task(vibration_pin));

// In joystick_read_task:
if btn_a_pressed {
    VIBRATION_SIGNAL.signal(VibrationPattern::Short);
}
```

### BLE Characteristic

```rust
// Option 1: Simple on/off/duration
#[characteristic(uuid = "...defa", write)]
vibration_control: u8,  // 0 = off, 1-255 = duration in 10ms units

// Option 2: Pattern control
#[characteristic(uuid = "...defa", write)]
vibration_pattern: u8,  // 0=off, 1=short, 2=medium, 3=long, 4=double, 5=triple
```

### Estimated Impact

- **Binary Size:** +1-2 KB (very simple GPIO)
- **Implementation Time:** 30-60 minutes
- **Difficulty:** ⭐⭐☆☆☆ (Easy, just GPIO output)

### Use Cases

1. **Button feedback** - Haptic confirmation on button press
2. **Game events** - Vibrate on collisions, achievements
3. **Notifications** - Alert user remotely via BLE
4. **Accessibility** - Tactile feedback for visually impaired users

---

## Combined Implementation

Implement all three features for a **full-featured gamepad**:

### BLE Service Layout

```
Service UUID: 12345678-1234-5678-1234-56789abcdef0

Characteristics:
├─ def1: X-Axis (u16, READ + NOTIFY)
├─ def2: Y-Axis (u16, READ + NOTIFY)
├─ def3: Button A (u8, READ + NOTIFY)
├─ def4: Button B (u8, READ + NOTIFY)
├─ def5: Button C (u8, READ + NOTIFY)
├─ def6: Button D (u8, READ + NOTIFY)
├─ def7: Button E (u8, READ + NOTIFY)
├─ def8: Button F (u8, READ + NOTIFY)
├─ def9: Buzzer Control (u8, WRITE)
└─ defa: Vibration Control (u8, WRITE)
```

### Total Impact

- **Binary Size:** ~148 KB / 512 KB (29% flash)
- **RAM:** ~44 KB / 128 KB (34%)
- **Implementation Time:** 3-4 hours total
- **Result:** Professional 6-button gamepad with audio + haptic feedback

---

## Implementation Order

### Recommended Approach: Incremental

**Phase 1:** Add 4 buttons (C, D, E, F)
- Low risk, same pattern as A/B
- Test thoroughly before moving on

**Phase 2:** Add vibration motor
- Simple GPIO, immediate feedback
- Enhances button press experience

**Phase 3:** Add buzzer
- More complex (PWM required)
- Adds audio dimension to gameplay

### Alternative: Minimal First

**Phase 1:** Add vibration only
- Quickest to implement
- Immediate UX improvement
- Test BLE write characteristics

**Phase 2:** Add buzzer
- Audio feedback complements haptic

**Phase 3:** Add 4 buttons
- Complete the gamepad

---

## Testing Checklist

### After Adding C, D, E, F Buttons:
- [ ] All 6 buttons log to RTT correctly
- [ ] All 6 BLE characteristics notify properly
- [ ] Web test page shows all 6 buttons
- [ ] Python script monitors all 6 buttons
- [ ] Binary size < 150 KB

### After Adding Buzzer:
- [ ] Buzzer plays tone when commanded via BLE
- [ ] Button press triggers buzzer beep (if local feedback)
- [ ] Frequency control works (if implemented)
- [ ] No audio glitches or stuttering

### After Adding Vibration:
- [ ] Motor vibrates on button press
- [ ] BLE write commands trigger vibration
- [ ] Pattern control works (if implemented)
- [ ] Motor stops cleanly (no stuck-on state)

---

## Troubleshooting

### Buttons C, D, E, F Not Reading

**Symptoms:** Always read as pressed or released

**Solutions:**
1. Try opposite pull resistor (Pull::Up vs Pull::Down)
2. Test with multimeter: Measure voltage when pressed/released
3. Check Joystick:bit documentation for button type
4. Verify P12-P15 are available (not used by other peripherals)

### Buzzer Not Working

**Symptoms:** No sound output

**Solutions:**
1. Verify P0 is configured as PWM output
2. Check PWM frequency (500-2000 Hz for most buzzers)
3. Ensure duty cycle is 50% (not 0% or 100%)
4. Test with simple test program before adding BLE

### Vibration Motor Stuck On

**Symptoms:** Motor won't stop vibrating

**Solutions:**
1. Ensure pin is set LOW in all code paths
2. Check for missed Timer::after() calls
3. Add explicit motor-off in disconnection handler
4. Implement safety timeout (max vibration duration)

---

## Reference Materials

### Pin Usage Summary

| Pin | Current Use | Expansion Use |
|-----|-------------|---------------|
| P0 | None | Buzzer (PWM) |
| P1 | Joystick X ✅ | - |
| P2 | Joystick Y ✅ | - |
| P12 | None | Button C |
| P13 | None | Button D |
| P14 | None | Button E |
| P15 | None | Button F |
| P16 | None | Vibration Motor |
| P0_14 | Button A ✅ | - |
| P0_23 | Button B ✅ | - |

### UUID Allocation

```
Service: 12345678-1234-5678-1234-56789abcdef0

Characteristics:
def1 - X-Axis ✅
def2 - Y-Axis ✅
def3 - Button A ✅
def4 - Button B ✅
def5 - Button C (available)
def6 - Button D (available)
def7 - Button E (available)
def8 - Button F (available)
def9 - Buzzer (available)
defa - Vibration (available)
defb-deff - Reserved for future use
```

---

## Questions to Consider

1. **Do you want BLE control of buzzer/vibration, or just local feedback?**
   - BLE control: More flexible, client can trigger feedback
   - Local feedback: Simpler, automatic on button press

2. **Should buzzer/vibration be enabled by default?**
   - Default ON: Better UX, immediate feedback
   - Default OFF: More battery efficient, user opt-in

3. **What's the priority order?**
   - All features: 3-4 hours total implementation
   - Buttons first: Most impactful for gameplay
   - Haptics first: Best immediate UX improvement

---

**Ready to implement?** Choose your preferred option and I'll generate the exact code changes needed!
