#![no_std]
#![no_main]

use defmt::{info, warn, error, Debug2Format};
use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use embassy_sync::signal::Signal;
use embassy_sync::blocking_mutex::raw::ThreadModeRawMutex;
use embassy_futures::select::select;
use microbit_bsp::{ble::MultiprotocolServiceLayer, display, Config, Microbit};
use trouble_host::prelude::*;
use {defmt_rtt as _, panic_probe as _};

// Joystick data structure for sharing between tasks
#[derive(Clone, Copy, Debug, defmt::Format)]
struct JoystickData {
    x: u16,       // 0-1023 range, center at 512
    y: u16,       // 0-1023 range, center at 512
    button_a: u8, // 0 = released, 1 = pressed
    button_b: u8, // 0 = released, 1 = pressed
}

// Global signal for joystick data (always latest value)
static JOYSTICK_SIGNAL: Signal<ThreadModeRawMutex, JoystickData> = Signal::new();

// Vibration pattern commands
#[derive(Clone, Copy, Debug, defmt::Format)]
enum VibrationPattern {
    Off,        // 0: No vibration
    Short,      // 1: 50ms pulse
    Medium,     // 2: 150ms pulse
    Long,       // 3: 300ms pulse
    Double,     // 4: Two 50ms pulses
    Triple,     // 5: Three 50ms pulses
}

impl VibrationPattern {
    fn from_u8(value: u8) -> Self {
        match value {
            0 => VibrationPattern::Off,
            1 => VibrationPattern::Short,
            2 => VibrationPattern::Medium,
            3 => VibrationPattern::Long,
            4 => VibrationPattern::Double,
            5 => VibrationPattern::Triple,
            _ => VibrationPattern::Off,
        }
    }
}

// Global signal for vibration commands
static VIBRATION_SIGNAL: Signal<ThreadModeRawMutex, VibrationPattern> = Signal::new();

// Max number of connections
const CONNECTIONS_MAX: usize = 1;

// Max number of L2CAP channels
const L2CAP_CHANNELS_MAX: usize = 2; // Signal + att

// BLE GATT Server definition
#[gatt_server]
struct JoystickServer {
    joystick_service: JoystickService,
}

// Custom Joystick Service with Buttons and Vibration
#[gatt_service(uuid = "12345678-1234-5678-1234-56789abcdef0")]
struct JoystickService {
    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef1", read, notify)]
    x_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef2", read, notify)]
    y_axis: u16,

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef3", read, notify)]
    button_a: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdef4", read, notify)]
    button_b: u8,  // 0 = released, 1 = pressed

    #[characteristic(uuid = "12345678-1234-5678-1234-56789abcdefa", write)]
    vibration_control: u8,  // 0=off, 1=short, 2=medium, 3=long, 4=double, 5=triple
}

#[embassy_executor::task]
async fn led_blink_task(mut display: display::LedMatrix<embassy_nrf::gpio::Output<'static>, 5, 5>) {
    info!("✓ LED matrix initialized");
    info!("Starting LED startup sequence...");

    // Create patterns for blinking using Frame directly
    let all_off = display::Frame::empty();

    let mut top_row = display::Frame::empty();
    top_row.set(0, 0);
    top_row.set(0, 1);
    top_row.set(0, 2);
    top_row.set(0, 3);
    top_row.set(0, 4);

    // Startup LED flash sequence - 3 quick blinks
    for i in 1..=3 {
        info!("Startup blink {}/3", i);
        display.display(top_row, Duration::from_millis(150)).await;
        display.display(all_off, Duration::from_millis(150)).await;
    }

    info!("✓ Startup complete!");
    info!("LED entering main blink loop...");

    // Main LED blink loop - slower to indicate system running
    loop {
        display.display(top_row, Duration::from_millis(500)).await;
        display.display(all_off, Duration::from_millis(500)).await;
    }
}

#[embassy_executor::task]
async fn vibration_task(mut vibration_pin: embassy_nrf::gpio::Output<'static>) {
    info!("✓ Vibration motor task started (P16)");
    info!("Motor is ACTIVE-LOW: LOW=ON, HIGH=OFF");
    info!("Patterns: 0=off, 1=short(50ms), 2=medium(150ms), 3=long(300ms), 4=double, 5=triple");

    loop {
        // Wait for vibration command
        let pattern = VIBRATION_SIGNAL.wait().await;

        info!("🔊 Vibration pattern: {:?}", pattern);

        match pattern {
            VibrationPattern::Off => {
                vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                info!("  → Motor OFF");
            }
            VibrationPattern::Short => {
                vibration_pin.set_low();   // INVERTED: LOW = motor ON
                Timer::after(Duration::from_millis(50)).await;
                vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                info!("  → Short pulse (50ms)");
            }
            VibrationPattern::Medium => {
                vibration_pin.set_low();   // INVERTED: LOW = motor ON
                Timer::after(Duration::from_millis(150)).await;
                vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                info!("  → Medium pulse (150ms)");
            }
            VibrationPattern::Long => {
                vibration_pin.set_low();   // INVERTED: LOW = motor ON
                Timer::after(Duration::from_millis(300)).await;
                vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                info!("  → Long pulse (300ms)");
            }
            VibrationPattern::Double => {
                for _ in 0..2 {
                    vibration_pin.set_low();   // INVERTED: LOW = motor ON
                    Timer::after(Duration::from_millis(50)).await;
                    vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                    Timer::after(Duration::from_millis(50)).await;
                }
                info!("  → Double pulse (2x 50ms)");
            }
            VibrationPattern::Triple => {
                for _ in 0..3 {
                    vibration_pin.set_low();   // INVERTED: LOW = motor ON
                    Timer::after(Duration::from_millis(50)).await;
                    vibration_pin.set_high();  // INVERTED: HIGH = motor OFF
                    Timer::after(Duration::from_millis(50)).await;
                }
                info!("  → Triple pulse (3x 50ms)");
            }
        }

        // Ensure motor is off after pattern (INVERTED: HIGH = OFF)
        vibration_pin.set_high();
    }
}

#[embassy_executor::task]
async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
    button_a: embassy_nrf::gpio::Input<'static>,
    button_b: embassy_nrf::gpio::Input<'static>,
) {
    info!("✓ Joystick ADC task started");
    info!("Joystick pins: P1 (X-axis), P2 (Y-axis)");
    info!("Buttons: A and B (from micro:bit board)");

    use embassy_nrf::saadc::{ChannelConfig, Config, Saadc, Resolution, Oversample};
    use embassy_nrf::bind_interrupts;

    bind_interrupts!(struct Irqs {
        SAADC => embassy_nrf::saadc::InterruptHandler;
    });

    // Create ADC configuration with better resolution
    let mut config = Config::default();
    config.resolution = Resolution::_12BIT;
    config.oversample = Oversample::OVER4X;

    // Initialize SAADC with 2 channels
    let mut adc = Saadc::new(
        saadc,
        Irqs,
        config,
        [
            ChannelConfig::single_ended(p1),
            ChannelConfig::single_ended(p2),
        ],
    );

    info!("✓ ADC channels configured");
    info!("✓ Buttons configured (active-low with pull-up from BSP)");
    info!("Calibrating joystick center position...");
    info!("Please do not touch the joystick during calibration...");

    // Take several samples to find center position
    let mut cal_buf = [0i16; 2];
    let mut x_cal_sum = 0i32;
    let mut y_cal_sum = 0i32;

    for _ in 0..10 {
        adc.sample(&mut cal_buf).await;
        x_cal_sum += cal_buf[0] as i32;
        y_cal_sum += cal_buf[1] as i32;
        Timer::after(Duration::from_millis(10)).await;
    }

    let x_center = (x_cal_sum / 10) as i16;
    let y_center = (y_cal_sum / 10) as i16;

    info!("✓ Calibration complete: X_center={}, Y_center={}", x_center, y_center);
    info!("Starting joystick readings (reading every 100ms)...");

    let mut buf = [0i16; 2];
    let mut count = 0u32;

    // Track previous button states for edge detection (haptic feedback)
    let mut btn_a_prev = false;
    let mut btn_b_prev = false;

    loop {
        // Read both ADC channels
        adc.sample(&mut buf).await;

        let x_raw = buf[0];
        let y_raw = buf[1];

        // Calculate deviation from calibrated center
        let x_delta = x_raw - x_center;
        let y_delta = y_raw - y_center;

        // Convert to 0-1023 range with center at 512
        // Assuming full range is about +/- 2000 from center
        let x_value = (512 + (x_delta as i32 * 512 / 2000).clamp(-512, 511)) as u16;
        let y_value = (512 + (y_delta as i32 * 512 / 2000).clamp(-512, 511)) as u16;

        // Calculate centered values (-512 to +511)
        let x_centered = x_value as i16 - 512;
        let y_centered = y_value as i16 - 512;

        count += 1;

        // Read button states (active-low: pressed = low = false)
        let btn_a_pressed = !button_a.is_high();
        let btn_b_pressed = !button_b.is_high();

        // Haptic feedback on button press (rising edge detection)
        if btn_a_pressed && !btn_a_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            info!("  🔊 Haptic feedback: Button A pressed");
        }
        if btn_b_pressed && !btn_b_prev {
            VIBRATION_SIGNAL.signal(VibrationPattern::Short);
            info!("  🔊 Haptic feedback: Button B pressed");
        }

        // Update previous button states
        btn_a_prev = btn_a_pressed;
        btn_b_prev = btn_b_pressed;

        // Send joystick data to BLE task via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: btn_a_pressed as u8,
            button_b: btn_b_pressed as u8,
        };
        JOYSTICK_SIGNAL.signal(joystick_data);

        // Log every 10th reading to reduce console output
        if count % 10 == 0 {
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

            // Detect significant movements (threshold = 150 from center, with deadzone of 50)
            let threshold = 150;
            let deadzone = 50;

            if x_centered.abs() > deadzone || y_centered.abs() > deadzone {
                if x_centered.abs() > threshold || y_centered.abs() > threshold {
                    if x_centered.abs() > y_centered.abs() {
                        // X-axis is inverted: positive = LEFT, negative = RIGHT
                        if x_centered > 0 {
                            info!("  → Movement: LEFT");
                        } else {
                            info!("  → Movement: RIGHT");
                        }
                    } else {
                        // Y-axis is inverted: positive = UP, negative = DOWN
                        if y_centered > 0 {
                            info!("  → Movement: UP");
                        } else {
                            info!("  → Movement: DOWN");
                        }
                    }
                }
            }

            // Log button press/release events
            if btn_a_pressed {
                info!("  🔘 Button A: PRESSED");
            }
            if btn_b_pressed {
                info!("  🔘 Button B: PRESSED");
            }
        }

        // Sample rate: 10Hz (100ms between readings)
        Timer::after(Duration::from_millis(100)).await;
    }
}

// MPSL task - required to run BLE stack
#[embassy_executor::task]
async fn mpsl_task(mpsl: &'static MultiprotocolServiceLayer<'static>) -> ! {
    mpsl.run().await
}

// BLE runner task - handles BLE protocol
async fn ble_runner_task<C: Controller, P: PacketPool>(
    mut runner: Runner<'_, C, P>,
) -> Result<(), BleHostError<C::Error>> {
    runner.run().await
}

// Advertise and wait for connection
async fn advertise<'a, 'b, C: Controller>(
    name: &'a str,
    peripheral: &mut Peripheral<'a, C, DefaultPacketPool>,
    server: &'b JoystickServer<'_>,
) -> Result<GattConnection<'a, 'b, DefaultPacketPool>, BleHostError<C::Error>> {
    let mut advertiser_data = [0; 31];
    AdStructure::encode_slice(
        &[
            AdStructure::Flags(LE_GENERAL_DISCOVERABLE | BR_EDR_NOT_SUPPORTED),
            AdStructure::CompleteLocalName(name.as_bytes()),
        ],
        &mut advertiser_data[..],
    )?;

    let advertiser = peripheral
        .advertise(
            &Default::default(),
            Advertisement::ConnectableScannableUndirected {
                adv_data: &advertiser_data[..],
                scan_data: &[],
            },
        )
        .await?;

    info!("[BLE] Advertising as '{}'...", name);
    let conn = advertiser.accept().await?.with_attribute_server(server)?;
    info!("[BLE] Connection established!");
    Ok(conn)
}

// Handle GATT connection and send joystick notifications
async fn connection_task<P: PacketPool>(server: &JoystickServer<'_>, conn: &GattConnection<'_, '_, P>) {
    let x_char = server.joystick_service.x_axis;
    let y_char = server.joystick_service.y_axis;
    let btn_a_char = server.joystick_service.button_a;
    let btn_b_char = server.joystick_service.button_b;
    let vibration_char = server.joystick_service.vibration_control;

    // Set initial values
    let _ = x_char.set(server, &512);
    let _ = y_char.set(server, &512);
    let _ = btn_a_char.set(server, &0);
    let _ = btn_b_char.set(server, &0);
    let _ = vibration_char.set(server, &0);

    info!("[BLE] Starting notification loop (joystick + buttons + vibration)...");

    let mut prev_vibration_value = 0u8;

    loop {
        // Use select to handle both GATT events and joystick updates
        let gatt_event_future = conn.next();
        let joystick_update_future = JOYSTICK_SIGNAL.wait();

        match select(gatt_event_future, joystick_update_future).await {
            embassy_futures::select::Either::First(event) => {
                match event {
                    GattConnectionEvent::Disconnected { reason } => {
                        info!("[BLE] Disconnected: {:?}", reason);
                        break;
                    }
                    GattConnectionEvent::Gatt { event } => {
                        match event.accept() {
                            Ok(reply) => reply.send().await,
                            Err(e) => warn!("[BLE] Error sending response: {:?}", e),
                        }
                    }
                    _ => {}
                }
            }
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
                        // New vibration command received
                        let pattern = VibrationPattern::from_u8(vibration_value);
                        info!("[BLE] 📝 Vibration command received: {:?}", pattern);
                        VIBRATION_SIGNAL.signal(pattern);

                        // Reset to 0 after processing
                        let _ = vibration_char.set(server, &0);
                        prev_vibration_value = 0;
                    } else {
                        prev_vibration_value = vibration_value;
                    }
                }
            }
        }
    }

    info!("[BLE] Connection task finished");
}

// Main BLE application task
async fn ble_app_task<C: Controller>(
    mut peripheral: Peripheral<'_, C, DefaultPacketPool>,
) {
    info!("[BLE] Creating GATT server...");

    let server = JoystickServer::new_with_config(GapConfig::Peripheral(PeripheralConfig {
        name: "microbit-joy",
        appearance: &appearance::power_device::GENERIC_POWER_DEVICE,
    }))
    .expect("Failed to create GATT server");

    info!("[BLE] GATT server created");

    loop {
        match advertise("microbit-joy", &mut peripheral, &server).await {
            Ok(conn) => {
                connection_task(&server, &conn).await;
            }
            Err(e) => {
                let e = Debug2Format(&e);
                warn!("[BLE] Advertising error: {:?}", e);
                Timer::after(Duration::from_secs(1)).await;
            }
        }
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    info!("=================================");
    info!("micro:bit v2 BLE Joystick");
    info!("=================================");

    let board = Microbit::new(Config::default());

    info!("Initializing peripherals...");

    // Spawn LED blink task
    match spawner.spawn(led_blink_task(board.display)) {
        Ok(_) => info!("✓ LED task spawned"),
        Err(_) => error!("✗ Failed to spawn LED task"),
    }

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

    // Spawn joystick reading task with ADC peripheral and pins
    info!("Spawning joystick task...");
    match spawner.spawn(joystick_read_task(board.saadc, board.p1, board.p2, board.btn_a, board.btn_b)) {
        Ok(_) => info!("✓ Joystick task spawned"),
        Err(_) => error!("✗ Failed to spawn joystick task"),
    }

    // Initialize BLE stack
    info!("Initializing BLE stack...");
    let (sdc, mpsl) = board
        .ble
        .init(board.timer0, board.rng)
        .expect("BLE Stack failed to initialize");

    // Spawn MPSL task
    spawner.must_spawn(mpsl_task(mpsl));
    info!("✓ MPSL task spawned");

    // Set up BLE host stack
    let address = Address::random([0x41, 0x5A, 0xE3, 0x1E, 0x10, 0xC9]);
    info!("BLE Address: {:?}", address);

    let mut resources: HostResources<DefaultPacketPool, CONNECTIONS_MAX, L2CAP_CHANNELS_MAX> =
        HostResources::new();
    let stack = trouble_host::new(sdc, &mut resources).set_random_address(address);

    let Host {
        peripheral,
        runner,
        ..
    } = stack.build();

    info!("✓ BLE Host stack created");
    info!("=================================");
    info!("✓ All tasks running!");
    info!("=================================");

    // Run BLE runner and application tasks concurrently
    select(ble_runner_task(runner), ble_app_task(peripheral)).await;
}
