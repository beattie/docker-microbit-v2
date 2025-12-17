//! Joystick and button input tasks

use defmt::info;
use embassy_time::{Duration, Timer};
// Import the signal and data type from gatt module
use crate::gatt::{JoystickData, JOYSTICK_SIGNAL};

#[embassy_executor::task]
pub async fn joystick_read_task(
    saadc: embassy_nrf::Peri<'static, embassy_nrf::peripherals::SAADC>,
    p1: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_03>,
    p2: embassy_nrf::Peri<'static, embassy_nrf::peripherals::P0_04>,
) {
    info!("✓ Joystick ADC task started");
    info!("Joystick pins: P1 (X-axis), P2 (Y-axis)");

    use embassy_nrf::bind_interrupts;
    use embassy_nrf::saadc::{ChannelConfig, Config, Oversample, Resolution, Saadc, VddInput};

    bind_interrupts!(struct Irqs {
        SAADC => embassy_nrf::saadc::InterruptHandler;
    });

    // Create ADC configuration with better resolution
    let mut config = Config::default();
    config.resolution = Resolution::_12BIT;
    config.oversample = Oversample::OVER4X;

    // Initialize SAADC with 3 channels
    let mut adc = Saadc::new(
        saadc,
        Irqs,
        config,
        [
            ChannelConfig::single_ended(p1),       // Channel 0: X-axis
            ChannelConfig::single_ended(p2),       // Channel 1: Y-axis
            ChannelConfig::single_ended(VddInput), // Channel 2: VDD (battery voltage)
        ],
    );

    info!("✓ ADC channels configured");
    info!("Calibrating joystick center position...");
    info!("Please do not touch the joystick during calibration...");

    // Take several samples to find center position
    let mut cal_buf = [0i16; 3];
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

    info!(
        "✓ Calibration complete: X_center={}, Y_center={}",
        x_center, y_center
    );
    info!("Starting joystick readings (reading every 100ms)...");

    let mut buf = [0i16; 3];
    let mut count = 0u32;

    loop {
        // Read all 3 ADC channels
        adc.sample(&mut buf).await;

        let x_raw = buf[0];
        let y_raw = buf[1];
        let vdd_raw = buf[2];

        // Calculate actual battery voltage from VDD reading
        // VDD channel uses 1/6 gain, 0.6V reference, 12-bit resolution
        // Formula: voltage_mv = (vdd_raw * 600 * 6) / 4095
        let voltage_mv = (vdd_raw as i32 * 600 * 6) / 4095;

        // Convert voltage to battery percentage (2.0V = 0%, 3.0V = 100%)
        let battery_level = if voltage_mv >= 3000 {
            100
        } else if voltage_mv <= 2000 {
            0
        } else {
            ((voltage_mv - 2000) * 100 / 1000) as u8
        };

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

        // Send joystick data to BLE task via signal
        let joystick_data = JoystickData {
            x: x_value,
            y: y_value,
            button_a: 0, // Will be updated by button_read_task
            button_b: 0, // Will be updated by button_read_task
            battery_level,
        };
        JOYSTICK_SIGNAL.signal(joystick_data);

        // Log every 10th reading to reduce console output
        if count % 10 == 0 {
            info!(
                "Joy {}: X={} (raw={} delta={} c={}), Y={} (raw={} delta={} c={}), Batt={}% ({}mV)",
                count / 5,
                x_value,
                x_raw,
                x_delta,
                x_centered,
                y_value,
                y_raw,
                y_delta,
                y_centered,
                battery_level,
                voltage_mv
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
        }

        // Sample rate: 10Hz (100ms between readings)
        Timer::after(Duration::from_millis(100)).await;
    }
}

#[embassy_executor::task]
pub async fn button_read_task(
    btn_a: embassy_nrf::gpio::Input<'static>,
    btn_b: embassy_nrf::gpio::Input<'static>,
) {
    use embassy_time::{Duration, Timer};

    info!("✓ Button task started");
    info!("Button pins configured from board (active-low)");

    loop {
        // Read button states (active-low: pressed = LOW)
        let a_pressed = if btn_a.is_low() { 1u8 } else { 0u8 };
        let b_pressed = if btn_b.is_low() { 1u8 } else { 0u8 };

        // Get current joystick data from signal
        let mut current_data = JOYSTICK_SIGNAL.wait().await;

        // Update button states
        current_data.button_a = a_pressed;
        current_data.button_b = b_pressed;

        // Send updated data back
        JOYSTICK_SIGNAL.signal(current_data);

        // 20ms sampling provides natural debouncing
        Timer::after(Duration::from_millis(20)).await;
    }
}
